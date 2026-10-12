import unittest
from unittest.mock import patch

from server.client_manager import ClientManager


class FakeSocket:
    pass


class ClientManagerHeartbeatTests(unittest.TestCase):
    def test_registering_udp_token_starts_heartbeat_deadline(self):
        clients = ClientManager()
        clients.add("Alice", FakeSocket())

        with patch("server.client_manager.time.monotonic", return_value=100.0):
            self.assertTrue(clients.register_udp_token("Alice", "session-token"))

        self.assertTrue(clients.udp_heartbeat_is_fresh("Alice", now=117.0, timeout=18.0))
        self.assertFalse(clients.udp_heartbeat_is_fresh("Alice", now=118.1, timeout=18.0))

    def test_udp_token_cannot_be_registered_for_unknown_user(self):
        clients = ClientManager()

        self.assertFalse(clients.register_udp_token("Unknown", "session-token"))


if __name__ == "__main__":
    unittest.main()
