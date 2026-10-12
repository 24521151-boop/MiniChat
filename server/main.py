import logging
import threading

from server.tcp_server import TCPServer
from server.udp_server import UDPServer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    tcp_server = TCPServer()
    udp_server = UDPServer(tcp_server.clients, tcp_server.handler)
    udp_thread = threading.Thread(target=udp_server.start, daemon=True, name="minichat-udp-server")
    udp_thread.start()
    try:
        tcp_server.start()
    except KeyboardInterrupt:
        print("\nĐang dừng MiniChat server...")
    finally:
        udp_server.stop()
        tcp_server.stop()
        udp_thread.join(timeout=1.5)


if __name__ == "__main__":
    main()
