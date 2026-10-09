import json
import logging
import re
import socket

from common.protocol import Message, MsgType, create_message
from server.client_manager import ClientManager

logger = logging.getLogger(__name__)
_USERNAME_RE = re.compile(r"^[\w.-]{1,24}$", re.UNICODE)


class MessageHandler:
    def __init__(self, clients: ClientManager) -> None:
        self.clients = clients

    def handle(self, conn: socket.socket, username: str | None, message: Message) -> str | None:
        if message.msg_type == MsgType.LOGIN:
            if username is not None:
                self._system(conn, "Bạn đã đăng nhập rồi.", event="ERROR")
                return username
            requested = message.payload.strip()
            if not _USERNAME_RE.fullmatch(requested):
                self._system(conn, "Tên người dùng phải có 1-24 ký tự: chữ, số, dấu gạch dưới, chấm hoặc gạch ngang.", event="LOGIN_ERROR")
                return None
            if not self.clients.add(requested, conn):
                self._system(conn, "Tên người dùng đã được sử dụng.", event="LOGIN_ERROR")
                return None
            self.clients.send(requested, create_message(MsgType.SYSTEM, payload=json.dumps({"event":"LOGIN_OK", "message":f"Xin chào {requested}!"}, ensure_ascii=False)))
            self.clients.publish_user_list()
            self.clients.broadcast(create_message(MsgType.SYSTEM, payload=json.dumps({"event":"NOTICE", "message":f"{requested} đã tham gia phòng chat."}, ensure_ascii=False)), exclude=requested)
            logger.info("User %s connected", requested)
            return requested

        if username is None:
            self._system(conn, "Vui lòng đăng nhập trước khi gửi tin nhắn.", event="ERROR")
            return None

        if message.msg_type == MsgType.LOGOUT:
            self.disconnect(username, conn)
            return None

        if message.msg_type == MsgType.CHAT_ALL:
            text = message.payload.strip()
            if not text:
                return username
            outgoing = create_message(MsgType.CHAT_ALL, sender=username, payload=text)
            self.clients.broadcast(outgoing)
            return username

        if message.msg_type == MsgType.CHAT_PRIVATE:
            text = message.payload.strip()
            recipient = message.receiver.strip()
            if not text:
                return username
            if recipient == username:
                self._system(conn, "Bạn không thể gửi tin nhắn riêng cho chính mình.", event="ERROR")
                return username
            if not self.clients.send(recipient, create_message(MsgType.CHAT_PRIVATE, sender=username, receiver=recipient, payload=text)):
                self._system(conn, f"Người dùng {recipient or '(chưa chọn)'} không tồn tại hoặc đã ngắt kết nối.", event="ERROR")
                return username
            self.clients.send(username, create_message(MsgType.CHAT_PRIVATE, sender=username, receiver=recipient, payload=text))
            return username

        self._system(conn, "Loại thông điệp không được hỗ trợ.", event="ERROR")
        return username

    def disconnect(self, username: str, conn: socket.socket) -> None:
        if not self.clients.remove(username, conn):
            return
        self.clients.publish_user_list()
        self.clients.broadcast(create_message(MsgType.SYSTEM, payload=json.dumps({"event":"NOTICE", "message":f"{username} đã rời phòng chat."}, ensure_ascii=False)))
        logger.info("User %s disconnected", username)

    @staticmethod
    def _system(conn: socket.socket, message: str, event: str = "NOTICE") -> None:
        raw = create_message(MsgType.SYSTEM, payload=json.dumps({"event":event, "message":message}, ensure_ascii=False))
        try:
            conn.sendall(raw.encode("utf-8"))
        except OSError:
            pass
