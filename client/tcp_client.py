import json
import socket
import threading
from queue import Queue
from typing import Any

from common.constants import BUFFER_SIZE, ENCODING, SERVER_IP, TCP_PORT
from common.protocol import MsgType, create_message

class TCPClient:
    """Small TCP client; network receiver threads never update the GUI directly."""

    def __init__(self, host: str = SERVER_IP, port: int = TCP_PORT) -> None:
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None
        self.incoming: Queue[dict[str, Any]] = Queue()
        self._send_lock = threading.Lock()
        self._receiver: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.username = ""

    def connect_and_login(self, username: str, timeout: float = 5.0) -> tuple[bool, str]:
        if self.socket is not None:
            return False, "Client đã kết nối."
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        self.socket = sock
        try:
            sock.connect((self.host, self.port))
            self.username = username.strip()
            self.send(MsgType.LOGIN, payload=self.username)
            data = bytearray()
            while b"\n" not in data:
                chunk = sock.recv(1)
                if not chunk:
                    raise ConnectionError("Server đã đóng kết nối.")
                data.extend(chunk)
                if len(data) > 65536:
                    raise ValueError("Phản hồi đăng nhập quá dài.")
            first_line, remainder = bytes(data).split(b"\n", 1)
            response = json.loads(first_line.decode(ENCODING))
            if response.get("type") != MsgType.SYSTEM.value:
                raise ValueError("Phản hồi đăng nhập không hợp lệ.")
            payload = json.loads(response.get("payload", "{}"))
            event = payload.get("event", "")
            message = payload.get("message", "")
            if event != "LOGIN_OK":
                self.close()
                return False, message or "Đăng nhập thất bại."
            sock.settimeout(None)
            self._receiver = threading.Thread(
                target=self._receive_loop,
                args=(remainder,),
                daemon=True,
                name="minichat-receiver",
            )
            self._receiver.start()
            return True, message or "Đăng nhập thành công."
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, ConnectionError) as exc:
            self.close()
            return False, str(exc) or "Không thể kết nối tới server."

    def send(self, msg_type: MsgType, receiver: str = "", payload: str = "") -> None:
        sock = self.socket
        if sock is None:
            raise ConnectionError("Chưa kết nối tới server.")
        raw = create_message(msg_type, sender=self.username, receiver=receiver, payload=payload)
        with self._send_lock:
            sock.sendall(raw.encode(ENCODING))

    def send_global(self, text: str) -> None:
        self.send(MsgType.CHAT_ALL, payload=text)

    def send_private(self, recipient: str, text: str) -> None:
        self.send(MsgType.CHAT_PRIVATE, receiver=recipient, payload=text)

    def logout(self) -> None:
        try:
            if self.socket is not None:
                self.send(MsgType.LOGOUT)
        except OSError:
            pass
        self.close()

    def close(self) -> None:
        self._stop_event.set()
        sock, self.socket = self.socket, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def _receive_loop(self, initial: bytes = b"") -> None:
        buffer = bytearray(initial)
        try:
            while not self._stop_event.is_set():
                if b"\n" in buffer:
                    line, _, remainder = buffer.partition(b"\n")
                    buffer = bytearray(remainder)
                    self._enqueue_line(line)
                    continue
                sock = self.socket
                if sock is None:
                    break
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                buffer.extend(chunk)
                if len(buffer) > 1_000_000 and b"\n" not in buffer:
                    self.incoming.put({"type": "SYSTEM", "payload": json.dumps({"event": "ERROR", "message": "Thông điệp nhận quá lớn."}, ensure_ascii=False)})
                    break
        except (OSError, UnicodeDecodeError) as exc:
            if not self._stop_event.is_set():
                self.incoming.put({"type": "SYSTEM", "payload": json.dumps({"event": "ERROR", "message": f"Mất kết nối tới server: {exc}"}, ensure_ascii=False)})
        finally:
            self._stop_event.set()
            self.incoming.put({"type": "_DISCONNECTED", "payload": ""})

    def _enqueue_line(self, line: bytes) -> None:
        if not line.strip():
            return
        try:
            item = json.loads(line.decode(ENCODING))
            if isinstance(item, dict):
                self.incoming.put(item)
        except json.JSONDecodeError:
            self.incoming.put({"type": "SYSTEM", "payload": json.dumps({"event": "ERROR", "message": "Server gửi dữ liệu không hợp lệ."}, ensure_ascii=False)})
