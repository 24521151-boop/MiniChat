import json
import logging
import socket
import threading
from queue import Queue
from typing import Any

from common.constants import ENCODING, SERVER_IP, UDP_PORT

logger = logging.getLogger(__name__)


class UDPClient:
    def __init__(self, token: str, host: str = SERVER_IP, port: int = UDP_PORT) -> None:
        self.token = token
        self.host = host
        self.port = port
        self.incoming: Queue[dict[str, Any]] = Queue()
        self._socket: socket.socket | None = None
        self._stop_event = threading.Event()
        self._send_lock = threading.Lock()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if self._socket is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        self._socket = sock
        self._threads = [
            threading.Thread(target=self._heartbeat_loop, daemon=True, name="minichat-udp-heartbeat"),
            threading.Thread(target=self._receive_loop, daemon=True, name="minichat-udp-receiver"),
        ]
        for thread in self._threads:
            thread.start()
        self._send({"type": "HEARTBEAT"})

    def send_typing(self, receiver: str, is_typing: bool) -> None:
        self._send({
            "type": "TYPING",
            "receiver": receiver,
            "typing": bool(is_typing),
        })

    def close(self) -> None:
        self._stop_event.set()
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        for thread in self._threads:
            if thread is not threading.current_thread():
                thread.join(timeout=1.2)
        self._threads.clear()

    def _send(self, data: dict[str, Any]) -> None:
        sock = self._socket
        if sock is None or self._stop_event.is_set():
            return
        packet = dict(data)
        packet["token"] = self.token
        try:
            encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode(ENCODING)
            with self._send_lock:
                sock.sendto(encoded, (self.host, self.port))
        except (OSError, TypeError, ValueError) as exc:
            if not self._stop_event.is_set():
                logger.debug("Could not send UDP datagram: %s", exc)

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.wait(5.0):
            self._send({"type": "HEARTBEAT"})

    def _receive_loop(self) -> None:
        while not self._stop_event.is_set():
            sock = self._socket
            if sock is None:
                break
            try:
                data, _address = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                if not self._stop_event.is_set():
                    logger.debug("UDP receive socket closed.")
                break
            try:
                message = json.loads(data.decode(ENCODING))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(message, dict) and message.get("type") == "TYPING":
                self.incoming.put(message)
