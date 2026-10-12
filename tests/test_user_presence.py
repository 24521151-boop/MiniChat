import json
import unittest

from common.protocol import MsgType
from server.client_manager import ClientManager


class FakeSocket:
    def __init__(self):
        self.sent = []

    def sendall(self, data: bytes):
        self.sent.append(data)

    def shutdown(self, _how):
        pass

    def close(self):
        pass


class UserPresenceTests(unittest.TestCase):
    def setUp(self):
        self.clients = ClientManager()
        self.alice = FakeSocket()
        self.bob = FakeSocket()

    def test_disconnected_user_remains_known_but_is_not_online(self):
        self.assertTrue(self.clients.add("Alice", self.alice))
        self.assertTrue(self.clients.add("Bob", self.bob))
        self.assertTrue(self.clients.remove("Bob", self.bob))

        self.assertEqual(self.clients.names(), ["Alice"])
        self.assertEqual(self.clients.known_names(), ["Alice", "Bob"])

    def test_user_list_publishes_known_and_online_names(self):
        self.clients.add("Alice", self.alice)
        self.clients.add("Bob", self.bob)
        self.clients.remove("Bob", self.bob)

        self.clients.publish_user_list()

        messages = [
            json.loads(line.decode("utf-8"))
            for chunk in self.alice.sent
            for line in chunk.splitlines()
            if line
        ]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["type"], MsgType.USER_LIST.value)
        payload = json.loads(messages[0]["payload"])
        self.assertEqual(payload, {
            "known": ["Alice", "Bob"],
            "online": ["Alice"],
        })

    def test_server_shutdown_clears_known_names(self):
        self.clients.add("Alice", self.alice)
        self.clients.add("Bob", self.bob)

        self.clients.close_all()

        self.assertEqual(self.clients.names(), [])
        self.assertEqual(self.clients.known_names(), [])


if __name__ == "__main__":
    unittest.main()
