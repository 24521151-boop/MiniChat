import json
import unittest

from common.protocol import Message, MsgType
from server.client_manager import ClientManager
from server.message_handler import MessageHandler


class FakeSocket:
    def __init__(self):
        self.sent = []

    def sendall(self, data: bytes):
        self.sent.append(data)

    def messages(self):
        result = []
        for chunk in self.sent:
            for line in chunk.splitlines():
                if line:
                    result.append(json.loads(line.decode("utf-8")))
        return result


class PrivateMessageRoutingTests(unittest.TestCase):
    def setUp(self):
        self.clients = ClientManager()
        self.handler = MessageHandler(self.clients)
        self.alice = FakeSocket()
        self.bob = FakeSocket()
        self.charlie = FakeSocket()
        self.clients.add("Alice", self.alice)
        self.clients.add("Bob", self.bob)
        self.clients.add("Charlie", self.charlie)

    def test_private_message_reaches_only_sender_and_recipient(self):
        message = Message(
            msg_type=MsgType.CHAT_PRIVATE,
            sender="Alice",
            receiver="Bob",
            payload="Nội dung riêng",
        )

        self.handler.handle(self.alice, "Alice", message)

        alice_messages = self.alice.messages()
        bob_messages = self.bob.messages()
        charlie_messages = self.charlie.messages()

        self.assertEqual(len(alice_messages), 1)
        self.assertEqual(len(bob_messages), 1)
        self.assertEqual(charlie_messages, [])
        self.assertEqual(alice_messages[0]["type"], MsgType.CHAT_PRIVATE.value)
        self.assertEqual(bob_messages[0]["type"], MsgType.CHAT_PRIVATE.value)
        self.assertEqual(alice_messages[0]["payload"], "Nội dung riêng")
        self.assertEqual(bob_messages[0]["payload"], "Nội dung riêng")

    def test_private_message_to_missing_user_is_not_broadcast(self):
        message = Message(
            msg_type=MsgType.CHAT_PRIVATE,
            sender="Alice",
            receiver="Nobody",
            payload="Nội dung riêng",
        )

        self.handler.handle(self.alice, "Alice", message)

        self.assertEqual(self.bob.messages(), [])
        self.assertEqual(self.charlie.messages(), [])
        self.assertTrue(any(
            item["type"] == MsgType.SYSTEM.value
            for item in self.alice.messages()
        ))


if __name__ == "__main__":
    unittest.main()
