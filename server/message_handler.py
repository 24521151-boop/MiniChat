import json
import logging
import re
import secrets
import socket
import threading

from common.protocol import Message, MsgType, create_message
from server.client_manager import ClientManager

logger = logging.getLogger(__name__)
_USERNAME_RE = re.compile(r"^[\w.-]{1,24}$", re.UNICODE)


class MessageHandler:
    def __init__(self, clients: ClientManager) -> None:
        self.clients = clients
        self._global_history: list[tuple[str, str]] = []
        self._history_limit = 500
        self._lock = threading.RLock()
        self._udp_tokens: dict[str, str] = {}

    def username_for_udp_token(self, token: str) -> str | None:
        with self._lock:
            for username, expected_token in self._udp_tokens.items():
                if secrets.compare_digest(expected_token, token):
                    return username
        return None

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
            udp_token = secrets.token_urlsafe(32)
            with self._lock:
                self._udp_tokens[requested] = udp_token
            self.clients.send(
                requested,
                create_message(
                    MsgType.SYSTEM,
                    payload=json.dumps({
                        "event": "LOGIN_OK",
                        "message": f"Xin chào {requested}!",
                        "udp_token": udp_token,
                    }, ensure_ascii=False),
                ),
            )
            with self._lock:
                history = list(self._global_history)
            for history_sender, history_text in history:
                self.clients.send(requested, create_message(MsgType.CHAT_ALL, sender=history_sender, payload=history_text))
            self.clients.publish_user_list()
            self.clients.broadcast(
                create_message(
                    MsgType.SYSTEM,
                    payload=json.dumps(
                        {"event": "NOTICE", "message": f"{requested} đã tham gia MiniChat."},
                        ensure_ascii=False,
                    ),
                ),
                exclude=requested,
            )
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
            with self._lock:
                self._append_history(self._global_history, (username, text))
            self.clients.broadcast(create_message(MsgType.CHAT_ALL, sender=username, payload=text))
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

    def _append_history(self, history: list[tuple[str, str]], entry: tuple[str, str]) -> None:
        history.append(entry)
        if len(history) > self._history_limit:
            del history[:-self._history_limit]

    def disconnect(self, username: str, conn: socket.socket) -> None:
        if not self.clients.remove(username, conn):
            return
        with self._lock:
            self._udp_tokens.pop(username, None)
        self.clients.publish_user_list()
        self.clients.broadcast(
            create_message(
                MsgType.SYSTEM,
                payload=json.dumps(
                    {"event": "NOTICE", "message": f"{username} đã ngắt kết nối."},
                    ensure_ascii=False,
                ),
            )
        )
        logger.info("User %s disconnected", username)

    @staticmethod
    def _system(conn: socket.socket, message: str, event: str = "NOTICE") -> None:
        raw = create_message(MsgType.SYSTEM, payload=json.dumps({"event": event, "message": message}, ensure_ascii=False))
        try:
            conn.sendall(raw.encode("utf-8"))
        except OSError:
            pass
