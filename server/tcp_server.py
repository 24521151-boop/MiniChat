import logging
import socket
import threading

from common.constants import BUFFER_SIZE, ENCODING, SERVER_IP, TCP_PORT
from common.protocol import parse_message
from server.client_manager import ClientManager
from server.message_handler import MessageHandler

logger = logging.getLogger(__name__)


class TCPServer:
    """TCP server that handles each client connection in a dedicated thread."""

    def __init__(self, host: str = "0.0.0.0", port: int = TCP_PORT) -> None:
        self.host = host
        self.port = port
        self.clients = ClientManager()
        self.handler = MessageHandler(self.clients)
        self._server_socket: socket.socket | None = None
        self._stop_event = threading.Event()
        self._threads: set[threading.Thread] = set()
        self._threads_lock = threading.Lock()

    def start(self) -> None:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen()
        server_sock.settimeout(1.0)
        self._server_socket = server_sock
        logger.info("MiniChat TCP server listening on %s:%s", self.host, self.port)
        print(f"MiniChat Server đang chạy tại {self.host}:{self.port}. Nhấn Ctrl+C để dừng.")
        try:
            while not self._stop_event.is_set():
                try:
                    conn, address = server_sock.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise
                thread = threading.Thread(
                    target=self._client_loop,
                    args=(conn, address),
                    daemon=True,
                    name=f"client-{address[0]}:{address[1]}",
                )
                with self._threads_lock:
                    self._threads.add(thread)
                thread.start()
        finally:
            self.stop()

    def stop(self) -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        with self._threads_lock:
            threads = list(self._threads)
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(timeout=1.0)
        logger.info("MiniChat server stopped.")

    def _client_loop(self, conn: socket.socket, address: tuple[str, int]) -> None:
        username: str | None = None
        buffer = bytearray()
        logger.info("Connection from %s:%s", *address)
        try:
            with conn:
                conn.settimeout(None)
                while not self._stop_event.is_set():
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if len(buffer) > 1_000_000 and b"\\n" not in buffer:
                        logger.warning("Oversized unterminated message from %s", address)
                        break
                    while b"\\n" in buffer:
                        line, _, remainder = buffer.partition(b"\\n")
                        buffer = bytearray(remainder)
                        if not line.strip():
                            continue
                        try:
                            decoded_line = line.decode(ENCODING)
                        except UnicodeDecodeError:
                            logger.warning("Invalid UTF-8 received from %s", address)
                            continue
                        message = parse_message(decoded_line)
                        if message is None:
                            continue
                        username = self.handler.handle(conn, username, message)
        except (ConnectionError, OSError) as exc:
            logger.info("Connection ended for %s: %s", address, exc)
        finally:
            if username is not None:
                self.handler.disconnect(username, conn)
            with self._threads_lock:
                self._threads.discard(threading.current_thread())
            logger.info("Connection closed: %s", address)
