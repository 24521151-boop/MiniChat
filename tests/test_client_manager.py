import threading
import unittest
from unittest.mock import patch

from server.client_manager import ClientManager


class FakeSocket:
    def __init__(self, block_send: bool = False):
        self.block_send = block_send
        self.send_started = threading.Event()
        self.release_send = threading.Event()
        self.sent = []

    def sendall(self, data: bytes):
        if self.block_send:
            self.send_started.set()
            if not self.release_send.wait(timeout=2):
                raise TimeoutError("Test socket send timed out")
        self.sent.append(data)


class ClientManagerTests(unittest.TestCase):
    def test_sending_to_one_client_does_not_block_another_client(self):
        clients = ClientManager()
        slow_client = FakeSocket(block_send=True)
        fast_client = FakeSocket()
        clients.add("Alice", slow_client)
        clients.add("Bob", fast_client)
        first_result = []
        second_result = []
        second_done = threading.Event()

        first_thread = threading.Thread(
            target=lambda: first_result.append(clients.send("Alice", "message to Alice"))
        )
        second_thread = threading.Thread(
            target=lambda: (
                second_result.append(clients.send("Bob", "message to Bob")),
                second_done.set(),
            )
        )

        try:
            first_thread.start()
            self.assertTrue(slow_client.send_started.wait(timeout=1))
            second_thread.start()
            completed_while_first_send_blocked = second_done.wait(timeout=0.5)
        finally:
            slow_client.release_send.set()
            first_thread.join(timeout=1)
            if second_thread.ident is not None:
                second_thread.join(timeout=1)

        self.assertTrue(completed_while_first_send_blocked)
        self.assertEqual(first_result, [True])
        self.assertEqual(second_result, [True])
        self.assertEqual(fast_client.sent, [b"message to Bob"])


class HeartbeatSocket:
    def sendall(self, _data: bytes):
        pass

    def shutdown(self, _how):
        pass

    def close(self):
        pass


class ClientManagerHeartbeatTests(unittest.TestCase):
    def test_registering_udp_token_starts_heartbeat_deadline(self):
        clients = ClientManager()
        clients.add("Alice", HeartbeatSocket())

        with patch("server.client_manager.time.monotonic", return_value=100.0):
            self.assertTrue(clients.register_udp_token("Alice", "session-token"))

        self.assertEqual(clients.expire_udp_heartbeats(now=117.0, timeout=18.0), [])
        self.assertEqual(clients.expire_udp_heartbeats(now=118.1, timeout=18.0), ["Alice"])

    def test_udp_token_cannot_be_registered_for_unknown_user(self):
        clients = ClientManager()

        self.assertFalse(clients.register_udp_token("Unknown", "session-token"))


if __name__ == "__main__":
    unittest.main()
