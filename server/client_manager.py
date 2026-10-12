import hmac
import json
import logging
import socket
import threading
import time
from typing import Optional

from common.constants import ENCODING
from common.protocol import MsgType, create_message

logger = logging.getLogger(__name__)


class ClientManager:
    """Owns shared client sessions and their TCP/UDP presence state."""

    def __init__(self) -> None:
        self._clients: dict[str, socket.socket] = {}
        self._known_users: set[str] = set()
        self._udp_tokens: dict[str, str] = {}
        self._udp_endpoints: dict[str, tuple[str, int]] = {}
        self._udp_last_seen: dict[str, float] = {}
        self._lock = threading.RLock()
        self._send_locks: dict[socket.socket, threading.Lock] = {}

    def add(self, username: str, conn: socket.socket) -> bool:
        with self._lock:
            if username in self._clients:
                return False
            self._clients[username] = conn
            self._known_users.add(username)
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

    def known_names(self) -> list[str]:
        with self._lock:
            return sorted(self._known_users, key=str.casefold)

    def _user_list_payload(self) -> str:
        with self._lock:
            online = sorted(self._clients, key=str.casefold)
            known = sorted(self._known_users, key=str.casefold)
        return json.dumps({"known": known, "online": online}, ensure_ascii=False)

    def get(self, username: str) -> Optional[socket.socket]:
        with self._lock:
            return self._clients.get(username)

    def _send_lock_for_locked(self, conn: socket.socket) -> threading.Lock:
        lock = self._send_locks.get(conn)
        if lock is None:
            lock = threading.Lock()
            self._send_locks[conn] = lock
        return lock

    def send(self, username: str, raw_message: str) -> bool:
        with self._lock:
            conn = self._clients.get(username)
            if conn is None:
                return False
            send_lock = self._send_lock_for_locked(conn)
        try:
            with send_lock:
                conn.sendall(raw_message.encode(ENCODING))
            return True
        except OSError:
            logger.info("Could not send message to %s", username)
            return False

    def send_to_connection(self, conn: socket.socket, raw_message: str) -> bool:
        with self._lock:
            send_lock = self._send_locks.get(conn)
            if send_lock is None and conn in self._clients.values():
                send_lock = self._send_lock_for_locked(conn)
        try:
            if send_lock is None:
                conn.sendall(raw_message.encode(ENCODING))
            else:
                with send_lock:
                    conn.sendall(raw_message.encode(ENCODING))
            return True
        except OSError:
            logger.info("Could not send message to connection")
            return False

    def broadcast(self, raw_message: str, exclude: Optional[str] = None) -> None:
        with self._lock:
            recipients = [
                (name, conn, self._send_lock_for_locked(conn))
                for name, conn in self._clients.items()
                if name != exclude
            ]
        failed: list[tuple[str, socket.socket]] = []
        data = raw_message.encode(ENCODING)
        for name, conn, send_lock in recipients:
            try:
                with send_lock:
                    conn.sendall(data)
            except OSError:
                failed.append((name, conn))
        for name, conn in failed:
            self.remove(name, conn)
        if failed:
            names_payload = self._user_list_payload()
            list_message = create_message(MsgType.USER_LIST, payload=names_payload).encode(ENCODING)
            with self._lock:
                remaining = [
                    (name, conn, self._send_lock_for_locked(conn))
                    for name, conn in self._clients.items()
                ]
            for name, conn, send_lock in remaining:
                try:
                    with send_lock:
                        conn.sendall(list_message)
                except OSError:
                    logger.info("Could not update user list for %s", name)

    def register_udp_token(self, username: str, token: str) -> bool:
        with self._lock:
            if username not in self._clients:
                return False
            self._udp_tokens[username] = token
            self._udp_endpoints.pop(username, None)
            self._udp_last_seen[username] = time.monotonic()
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
                    if name in self._clients and expected and hmac.compare_digest(expected, token)
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

    def release_connection(self, conn: socket.socket) -> None:
        with self._lock:
            self._send_locks.pop(conn, None)

    def close_all(self) -> None:
        """Close every active socket during server shutdown."""
        with self._lock:
            clients = list(self._clients.items())
            self._clients.clear()
            self._udp_tokens.clear()
            self._udp_endpoints.clear()
            self._udp_last_seen.clear()
            self._known_users.clear()
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
        payload = self._user_list_payload()
        self.broadcast(create_message(MsgType.USER_LIST, payload=payload))

