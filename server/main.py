import logging

from server.tcp_server import TCPServer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    server = TCPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nĐang dừng MiniChat server...")
        server.stop()


if __name__ == "__main__":
    main()
