import logging
import socket
import threading

from common.constants import BUFFER_SIZE, ENCODING, UDP_PORT
from server.client_manager import ClientManager
from server.message_handler import MessageHandler
from server.udp_message_handler import UDPMessageHandler

logger = logging.getLogger(__name__)


class UDPServer:
    def __init__(
        self,
        clients: ClientManager,
        tcp_handler: MessageHandler,
        host: str = "0.0.0.0",
        port: int = UDP_PORT,
    ) -> None:
        self.clients = clients
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None
        self._stop_event = threading.Event()
        self._send_lock = threading.Lock()
        self.handler = UDPMessageHandler(clients, tcp_handler, self._send_to)

    def start(self) -> None:
        if self._socket is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        sock.settimeout(1.0)
        self._socket = sock
        logger.info("MiniChat UDP server listening on %s:%s", self.host, self.port)
        print(f"MiniChat UDP đang chạy tại {self.host}:{self.port}.")
        try:
            while not self._stop_event.is_set():
                try:
                    data, address = sock.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    self.handler.check_timeouts()
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise
                self.handler.handle_datagram(data, address)
                self.handler.check_timeouts()
        finally:
            self.stop()

    def stop(self) -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        logger.info("MiniChat UDP server stopped.")

    def _send_to(self, payload: bytes, address: tuple[str, int]) -> None:
        sock = self._socket
        if sock is None or self._stop_event.is_set():
            return
        try:
            with self._send_lock:
                sock.sendto(payload, address)
        except OSError as exc:
            logger.debug("Could not send UDP datagram to %s: %s", address, exc)
