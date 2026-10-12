import json
import logging
import socket
import threading
import time
from typing import Callable

from common.constants import ENCODING
from server.client_manager import ClientManager
from server.message_handler import MessageHandler

logger = logging.getLogger(__name__)
_HEARTBEAT_TIMEOUT = 18.0


class UDPMessageHandler:
    def __init__(
        self,
        clients: ClientManager,
        tcp_handler: MessageHandler,
        send_to: Callable[[bytes, tuple[str, int]], None],
    ) -> None:
        self.clients = clients
        self.tcp_handler = tcp_handler
        self.send_to = send_to
        self._endpoints: dict[str, tuple[str, int]] = {}
        self._last_seen: dict[str, float] = {}
        self._lock = threading.RLock()

    def handle_datagram(self, data: bytes, address: tuple[str, int]) -> None:
        if len(data) > 4096:
            return
        try:
            packet = json.loads(data.decode(ENCODING))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(packet, dict):
            return

        token = packet.get("token")
        if not isinstance(token, str) or not token:
            return
        username = self.tcp_handler.username_for_udp_token(token)
        if username is None or self.clients.get(username) is None:
            return

        packet_type = packet.get("type")
        if packet_type == "HEARTBEAT":
            with self._lock:
                self._endpoints[username] = address
                self._last_seen[username] = time.monotonic()
            return

        if packet_type != "TYPING":
            return
        with self._lock:
            endpoint = self._endpoints.get(username)
            last_seen = self._last_seen.get(username)
        if endpoint != address or last_seen is None or time.monotonic() - last_seen > _HEARTBEAT_TIMEOUT:
            return

        receiver = packet.get("receiver", "")
        is_typing = packet.get("typing")
        if not isinstance(receiver, str) or not isinstance(is_typing, bool):
            return
        notice = json.dumps({
            "type": "TYPING",
            "sender": username,
            "receiver": receiver,
            "typing": is_typing,
        }, ensure_ascii=False, separators=(",", ":")).encode(ENCODING)

        with self._lock:
            if receiver:
                recipients = [(receiver, self._endpoints.get(receiver))]
            else:
                recipients = [
                    (name, endpoint)
                    for name, endpoint in self._endpoints.items()
                    if name != username
                ]
        for recipient, target in recipients:
            if recipient == username or self.clients.get(recipient) is None or target is None:
                continue
            self.send_to(notice, target)

    def check_timeouts(self) -> None:
        now = time.monotonic()
        with self._lock:
            stale = [
                username for username, last_seen in self._last_seen.items()
                if now - last_seen > _HEARTBEAT_TIMEOUT
            ]
            for username in stale:
                self._last_seen.pop(username, None)
                self._endpoints.pop(username, None)

        for username in stale:
            conn = self.clients.get(username)
            if conn is not None:
                logger.info("UDP heartbeat timed out for %s; closing TCP session", username)
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except OSError:
                    try:
                        conn.close()
                    except OSError:
                        pass

