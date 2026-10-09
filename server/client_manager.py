import json
import logging
import socket
import threading
from typing import Optional

from common.constants import ENCODING
from common.protocol import MsgType, create_message

logger = logging.getLogger(__name__)


class ClientManager:
    """Thread-safe registry of authenticated client connections."""

    def __init__(self) -> None:
        self._clients: dict[str, socket.socket] = {}
        self._lock = threading.RLock()

    def add(self, username: str, conn: socket.socket) -> bool:
        with self._lock:
            if username in self._clients:
                return False
            self._clients[username] = conn
            return True

    def remove(self, username: str, conn: Optional[socket.socket] = None) -> bool:
        with self._lock:
            current = self._clients.get(username)
            if current is None or (conn is not None and current is not conn):
                return False
            del self._clients[username]
            return True

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._clients.keys(), key=str.casefold)

    def get(self, username: str) -> Optional[socket.socket]:
        with self._lock:
            return self._clients.get(username)

    def send(self, username: str, raw_message: str) -> bool:
        with self._lock:
            conn = self._clients.get(username)
        if conn is None:
            return False
        try:
            conn.sendall(raw_message.encode(ENCODING))
            return True
        except OSError:
            logger.info("Could not send message to %s", username)
            return False

    def broadcast(self, raw_message: str, exclude: Optional[str] = None) -> None:
        with self._lock:
            recipients = [(name, conn) for name, conn in self._clients.items() if name != exclude]
        failed: list[tuple[str, socket.socket]] = []
        data = raw_message.encode(ENCODING)
        for name, conn in recipients:
            try:
                conn.sendall(data)
            except OSError:
                failed.append((name, conn))
        for name, conn in failed:
            self.remove(name, conn)

    def publish_user_list(self) -> None:
        payload = json.dumps(self.names(), ensure_ascii=False)
        self.broadcast(create_message(MsgType.USER_LIST, payload=payload))
