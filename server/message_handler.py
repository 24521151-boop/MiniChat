import json
import logging
import re
import socket
import threading

from common.protocol import Message, MsgType, create_message
from server.client_manager import ClientManager

logger = logging.getLogger(__name__)
_USERNAME_RE = re.compile(r"^[\w.-]{1,24}$", re.UNICODE)
_ROOM_NAME_RE = re.compile(r"^[^\r\n]{1,40}$")


class MessageHandler:
    def __init__(self, clients: ClientManager) -> None:
        self.clients = clients
        self._global_history: list[tuple[str, str]] = []
        self._rooms: dict[str, dict] = {}
        self._history_limit = 500
        self._lock = threading.RLock()

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
            self.clients.send(requested, create_message(MsgType.SYSTEM, payload=json.dumps({"event": "LOGIN_OK", "message": f"Xin chào {requested}!"}, ensure_ascii=False)))
            with self._lock:
                global_history = list(self._global_history)
                room_names = [
                    name for name, room in self._rooms.items()
                    if requested in room["members"]
                ]
            for history_sender, history_text in global_history:
                self.clients.send(requested, create_message(MsgType.CHAT_ALL, sender=history_sender, payload=history_text))
            self._send_room_list(requested)
            for room_name in room_names:
                self._send_room_history(requested, room_name)
            self.clients.publish_user_list()
            self.clients.broadcast(create_message(MsgType.SYSTEM, payload=json.dumps({"event": "NOTICE", "message": f"{requested} đã tham gia phòng chat."}, ensure_ascii=False)), exclude=requested)
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

        if message.msg_type == MsgType.CREATE_ROOM:
            self._create_room(username, message.payload, conn)
            return username

        if message.msg_type == MsgType.ADD_MEMBER:
            self._add_member(username, message.receiver, message.payload, conn)
            return username

        if message.msg_type == MsgType.CHAT_ROOM:
            self._send_room_message(username, message.receiver, message.payload, conn)
            return username

        self._system(conn, "Loại thông điệp không được hỗ trợ.", event="ERROR")
        return username

    def _create_room(self, username: str, raw_name: str, conn: socket.socket) -> None:
        room_name = raw_name.strip()
        if not _ROOM_NAME_RE.fullmatch(room_name):
            self._system(conn, "Tên phòng phải có từ 1 đến 40 ký tự và không được xuống dòng.", event="ERROR")
            return
        with self._lock:
            if any(name.casefold() == room_name.casefold() for name in self._rooms):
                self._system(conn, "Tên phòng này đã tồn tại.", event="ERROR")
                return
            self._rooms[room_name] = {
                "owner": username,
                "members": {username},
                "history": [],
            }
            notice = f"{username} đã tạo phòng \"{room_name}\"."
            self._append_history(self._global_history, ("Hệ thống", notice))
        self._send_room_list(username)
        self.clients.broadcast(create_message(MsgType.CHAT_ALL, sender="Hệ thống", payload=notice))

    def _add_member(self, username: str, raw_member: str, raw_room: str, conn: socket.socket) -> None:
        member = raw_member.strip()
        room_name = raw_room.strip()
        if not _USERNAME_RE.fullmatch(member):
            self._system(conn, "Tên đăng nhập thành viên không hợp lệ.", event="ERROR")
            return
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None:
                self._system(conn, "Không tìm thấy phòng chat.", event="ERROR")
                return
            if room["owner"] != username:
                self._system(conn, "Chỉ người tạo phòng mới có quyền thêm thành viên.", event="ERROR")
                return
            if member in room["members"]:
                self._system(conn, f"{member} đã là thành viên của phòng.", event="ERROR")
                return
            room["members"].add(member)
            notice = f"{member} đã được {username} thêm vào phòng \"{room_name}\"."
            self._append_history(room["history"], ("Hệ thống", notice))
            members = list(room["members"])
        for room_member in members:
            self._send_room_list(room_member)
        if self.clients.get(member) is not None:
            self._send_room_history(member, room_name)
        raw_notice = create_message(MsgType.CHAT_ROOM, sender="Hệ thống", receiver=room_name, payload=notice)
        for room_member in members:
            if room_member != member:
                self.clients.send(room_member, raw_notice)

    def _send_room_message(self, username: str, room_name: str, raw_text: str, conn: socket.socket) -> None:
        text = raw_text.strip()
        room_name = room_name.strip()
        if not text:
            return
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or username not in room["members"]:
                self._system(conn, "Bạn không phải thành viên của phòng này.", event="ERROR")
                return
            self._append_history(room["history"], (username, text))
            members = list(room["members"])
        outgoing = create_message(MsgType.CHAT_ROOM, sender=username, receiver=room_name, payload=text)
        for member in members:
            self.clients.send(member, outgoing)

    def _send_room_list(self, username: str) -> None:
        with self._lock:
            rooms = [
                {
                    "name": name,
                    "owner": room["owner"],
                    "members": sorted(room["members"], key=str.casefold),
                }
                for name, room in self._rooms.items()
                if username in room["members"]
            ]
        payload = json.dumps(rooms, ensure_ascii=False)
        self.clients.send(username, create_message(MsgType.ROOM_LIST, payload=payload))

    def _send_room_history(self, username: str, room_name: str) -> None:
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or username not in room["members"]:
                return
            history = list(room["history"])
        for sender, text in history:
            self.clients.send(username, create_message(MsgType.CHAT_ROOM, sender=sender, receiver=room_name, payload=text))

    def _append_history(self, history: list[tuple[str, str]], entry: tuple[str, str]) -> None:
        history.append(entry)
        if len(history) > self._history_limit:
            del history[:-self._history_limit]

    def disconnect(self, username: str, conn: socket.socket) -> None:
        if not self.clients.remove(username, conn):
            return
        self.clients.publish_user_list()
        self.clients.broadcast(create_message(MsgType.SYSTEM, payload=json.dumps({"event": "NOTICE", "message": f"{username} đã rời phòng chat."}, ensure_ascii=False)))
        logger.info("User %s disconnected", username)

    @staticmethod
    def _system(conn: socket.socket, message: str, event: str = "NOTICE") -> None:
        raw = create_message(MsgType.SYSTEM, payload=json.dumps({"event": event, "message": message}, ensure_ascii=False))
        try:
            conn.sendall(raw.encode("utf-8"))
        except OSError:
            pass
