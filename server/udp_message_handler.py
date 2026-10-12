import json
import logging
import socket
import time
from typing import Callable

from common.constants import ENCODING
from server.client_manager import ClientManager
from server.tcp_message_handler import TCPMessageHandler

logger = logging.getLogger(__name__)
_HEARTBEAT_TIMEOUT = 18.0


class UDPMessageHandler:
    """Handles UDP heartbeat and typing messages using shared client state."""

    def __init__(
        self,
        clients: ClientManager,
        tcp_handler: TCPMessageHandler,
        send_to: Callable[[bytes, tuple[str, int]], None],
    ) -> None:
        self.clients = clients
        self.tcp_handler = tcp_handler
        self.send_to = send_to
        self._timed_out: set[str] = set()

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
        packet_type = packet.get("type")

        if packet_type == "HEARTBEAT":
            username = self.clients.register_udp_heartbeat(token, address, time.monotonic())
            if username is not None:
                self._timed_out.discard(username)
            return

        username = self.clients.authenticate_udp_token(token)
        if username is None:
            return
        if self.clients.get_udp_endpoint(username) != address:
            return
        if not self.clients.udp_heartbeat_is_fresh(username, time.monotonic(), _HEARTBEAT_TIMEOUT):
            return
        if packet_type != "TYPING":
            return

        receiver = packet.get("receiver", "")
        is_typing = packet.get("typing")
        if not isinstance(receiver, str) or not isinstance(is_typing, bool):
            return
        if receiver and receiver == username:
            return

        notice = json.dumps({
            "type": "TYPING",
            "sender": username,
            "receiver": receiver,
            "typing": is_typing,
        }, ensure_ascii=False, separators=(",", ":")).encode(ENCODING)

        if receiver:
            endpoint = self.clients.get_udp_endpoint(receiver)
            if endpoint is not None and self.clients.get(receiver) is not None:
                self.send_to(notice, endpoint)
            return

        for recipient, endpoint in self.clients.udp_recipients(exclude=username):
            self.send_to(notice, endpoint)

    def check_timeouts(self) -> None:
        now = time.monotonic()
        expired = self.clients.expired_udp_heartbeats(now, _HEARTBEAT_TIMEOUT)
        for username in expired:
            if username in self._timed_out:
                continue
            conn = self.clients.get(username)
            if conn is None:
                self._timed_out.add(username)
                continue
            self._timed_out.add(username)
            logger.info("UDP heartbeat timed out for %s; closing TCP session", username)
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                try:
                    conn.close()
                except OSError:
                    pass
