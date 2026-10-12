import json
import time
from typing import Callable

from common.constants import ENCODING
from server.client_manager import ClientManager

MAX_DATAGRAM_SIZE = 4096


class UDPMessageHandler:
    """Processes UDP heartbeat and typing datagrams only."""

    def __init__(
        self,
        clients: ClientManager,
        send_to: Callable[[bytes, tuple[str, int]], None],
    ) -> None:
        self.clients = clients
        self.send_to = send_to

    def handle_datagram(self, data: bytes, address: tuple[str, int]) -> None:
        if len(data) > MAX_DATAGRAM_SIZE:
            return
        try:
            packet = json.loads(data.decode(ENCODING))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(packet, dict):
            return

        token = packet.get("token")
        packet_type = packet.get("type")
        if not isinstance(token, str) or not token:
            return

        if packet_type == "HEARTBEAT":
            self.clients.register_udp_heartbeat(token, address, time.monotonic())
            return

        if packet_type != "TYPING":
            return

        username = self.clients.authenticate_udp_token(token)
        if username is None:
            return
        if not self.clients.is_valid_udp_endpoint(username, address, time.monotonic()):
            return

        receiver = packet.get("receiver", "")
        is_typing = packet.get("typing")
        if not isinstance(receiver, str) or not isinstance(is_typing, bool):
            return
        if receiver and receiver == username:
            return

        notice = json.dumps(
            {
                "type": "TYPING",
                "sender": username,
                "receiver": receiver,
                "typing": is_typing,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode(ENCODING)

        if receiver:
            endpoint = self.clients.get_udp_endpoint(receiver)
            if endpoint is not None and self.clients.get(receiver) is not None:
                self.send_to(notice, endpoint)
            return

        for _recipient, endpoint in self.clients.udp_recipients(exclude=username):
            self.send_to(notice, endpoint)
