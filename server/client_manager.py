import hmac
import json
import logging
import socket
import threading
from typing import Optional

from common.constants import ENCODING
from common.protocol import MsgType, create_message

logger = logging.getLogger(__name__)


class ClientManager:
    """Owns shared client sessions and their TCP/UDP presence state."""

    def __init__(self) -> None:
        self._clients: dict[str, socket.socket] = {}
        self._udp_tokens: dict[str, str] = {}
        self._udp_endpoints: dict[str, tuple[str, int]] = {}
        self._udp_last_seen: dict[str, float] = {}
        self._lock = threading.RLock()
        self._send_lock = threading.Lock()

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
            self._udp_tokens.pop(username, None)
            self._udp_endpoints.pop(username, None)
            self._udp_last_seen.pop(username, None)
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
            with self._send_lock:
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
                with self._send_lock:
                    conn.sendall(data)
            except OSError:
                failed.append((name, conn))
        for name, conn in failed:
            self.remove(name, conn)
        if failed:
            names_payload = json.dumps(self.names(), ensure_ascii=False)
            list_message = create_message(MsgType.USER_LIST, payload=names_payload).encode(ENCODING)
            with self._lock:
                remaining = list(self._clients.items())
            for name, conn in remaining:
                try:
                    with self._send_lock:
                        conn.sendall(list_message)
                except OSError:
                    logger.info("Could not update user list for %s", name)

    def register_udp_token(self, username: str, token: str) -> bool:
        with self._lock:
            if username not in self._clients:
                return False
            self._udp_tokens[username] = token
            self._udp_endpoints.pop(username, None)
            self._udp_last_seen.pop(username, None)
            return True

    def authenticate_udp_token(self, token: str) -> Optional[str]:
        with self._lock:
            for username, expected in self._udp_tokens.items():
                if username in self._clients and expected and hmac.compare_digest(expected, token):
                    return username
        return None

    def register_udp_heartbeat(
        self, token: str, address: tuple[str, int], now: float
    ) -> Optional[str]:
        with self._lock:
            username = next(
                (
                    name for name, expected in self._udp_tokens.items()
                    if name in self._clients and expected and secrets_compare(expected, token)
                ),
                None,
            )
            if username is None:
                return None
            self._udp_endpoints[username] = address
            self._udp_last_seen[username] = now
            return username

    def get_udp_endpoint(self, username: str) -> Optional[tuple[str, int]]:
        with self._lock:
            return self._udp_endpoints.get(username)

    def is_valid_udp_endpoint(
        self, username: str, address: tuple[str, int], now: float, timeout: float = 18.0
    ) -> bool:
        with self._lock:
            last_seen = self._udp_last_seen.get(username)
            return (
                username in self._clients
                and self._udp_endpoints.get(username) == address
                and last_seen is not None
                and now - last_seen <= timeout
            )

    def udp_recipients(self, exclude: Optional[str] = None) -> list[tuple[str, tuple[str, int]]]:
        with self._lock:
            return [
                (username, endpoint)
                for username, endpoint in self._udp_endpoints.items()
                if username != exclude and username in self._clients
            ]

    def udp_heartbeat_is_fresh(self, username: str, now: float, timeout: float) -> bool:
        with self._lock:
            last_seen = self._udp_last_seen.get(username)
            return username in self._clients and last_seen is not None and now - last_seen <= timeout

    def expire_udp_heartbeats(self, now: float, timeout: float) -> list[str]:
        """Close TCP sessions whose UDP heartbeat has expired.

        TCP connection threads remain responsible for final session removal and
        broadcasting the updated online-user list.
        """
        with self._lock:
            expired = [
                (username, self._clients.get(username), last_seen)
                for username, last_seen in self._udp_last_seen.items()
                if username in self._clients and now - last_seen > timeout
            ]
            for username, _conn, _last_seen in expired:
                self._udp_last_seen.pop(username, None)
                self._udp_endpoints.pop(username, None)
                self._udp_tokens.pop(username, None)

        closed: list[str] = []
        for username, conn, _last_seen in expired:
            if conn is None:
                continue
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass
            logger.info("UDP heartbeat expired; closed TCP session for %s", username)
            closed.append(username)
        return closed

    def close_all(self) -> None:
        """Close every active socket during server shutdown."""
        with self._lock:
            clients = list(self._clients.items())
            self._clients.clear()
            self._udp_tokens.clear()
            self._udp_endpoints.clear()
            self._udp_last_seen.clear()
        for username, conn in clients:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass
            logger.info("Closed connection for %s during server shutdown", username)

    def publish_user_list(self) -> None:
        payload = json.dumps(self.names(), ensure_ascii=False)
        self.broadcast(create_message(MsgType.USER_LIST, payload=payload))

