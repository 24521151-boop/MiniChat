import json
import unittest

from server.client_manager import ClientManager
from server.udp_message_handler import UDPMessageHandler


class FakeSocket:
    def sendall(self, _data: bytes):
        pass


class UDPMessageHandlerTests(unittest.TestCase):
    def setUp(self):
        self.clients = ClientManager()
        self.alice = FakeSocket()
        self.bob = FakeSocket()
        self.clients.add("Alice", self.alice)
        self.clients.add("Bob", self.bob)
        self.clients.register_udp_token("Alice", "alice-session-token")
        self.clients.register_udp_token("Bob", "bob-session-token")
        self.sent = []
        self.handler = UDPMessageHandler(
            self.clients,
            lambda payload, address: self.sent.append((json.loads(payload.decode("utf-8")), address)),
        )
        self.alice_address = ("127.0.0.1", 51001)
        self.bob_address = ("127.0.0.1", 51002)

    def send_packet(self, token, address, packet_type, **extra):
        packet = {"token": token, "type": packet_type, **extra}
        self.handler.handle_datagram(json.dumps(packet).encode("utf-8"), address)

    def test_heartbeat_registers_endpoint_in_client_manager(self):
        self.send_packet("alice-session-token", self.alice_address, "HEARTBEAT")
        self.assertEqual(self.clients.get_udp_endpoint("Alice"), self.alice_address)

    def test_typing_is_forwarded_to_other_registered_users(self):
        self.send_packet("alice-session-token", self.alice_address, "HEARTBEAT")
        self.send_packet("bob-session-token", self.bob_address, "HEARTBEAT")
        self.send_packet("alice-session-token", self.alice_address, "TYPING", receiver="", typing=True)

        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0][0]["type"], "TYPING")
        self.assertEqual(self.sent[0][0]["sender"], "Alice")
        self.assertTrue(self.sent[0][0]["typing"])
        self.assertEqual(self.sent[0][1], self.bob_address)

    def test_typing_from_unregistered_endpoint_is_ignored(self):
        self.send_packet("alice-session-token", ("127.0.0.1", 59999), "TYPING", receiver="", typing=True)
        self.assertEqual(self.sent, [])

    def test_removing_user_clears_udp_state(self):
        self.send_packet("alice-session-token", self.alice_address, "HEARTBEAT")
        self.assertTrue(self.clients.remove("Alice", self.alice))
        self.assertIsNone(self.clients.get_udp_endpoint("Alice"))
        self.assertIsNone(self.clients.authenticate_udp_token("alice-session-token"))


if __name__ == "__main__":
    unittest.main()
