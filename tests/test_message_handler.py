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


class MessageHandlerTests(unittest.TestCase):
    def setUp(self):
        self.clients = ClientManager()
        self.handler = MessageHandler(self.clients)
        self.alice = FakeSocket()
        self.clients.add("Alice", self.alice)

    def send(self, username, conn, msg_type, receiver="", payload=""):
        message = Message(
            msg_type=msg_type,
            sender=username,
            receiver=receiver,
            payload=payload,
        )
        self.handler.handle(conn, username, message)

    def test_late_login_receives_global_history(self):
        self.send("Alice", self.alice, MsgType.CHAT_ALL, payload="Tin nhắn chung trước đó")

        bob = FakeSocket()
        login = Message(
            msg_type=MsgType.LOGIN,
            payload="Bob",
        )
        self.handler.handle(bob, None, login)

        messages = bob.messages()
        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ALL.value
            and item["sender"] == "Alice"
            and item["payload"] == "Tin nhắn chung trước đó"
            for item in messages
        ))

    def test_global_message_is_broadcast_and_kept_in_history(self):
        bob = FakeSocket()
        self.clients.add("Bob", bob)

        self.send("Alice", self.alice, MsgType.CHAT_ALL, payload="Xin chào cả nhóm")

        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ALL.value
            and item["payload"] == "Xin chào cả nhóm"
            for item in self.alice.messages()
        ))
        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ALL.value
            and item["payload"] == "Xin chào cả nhóm"
            for item in bob.messages()
        ))

    def test_private_message_is_not_broadcast_to_other_users(self):
        bob = FakeSocket()
        charlie = FakeSocket()
        self.clients.add("Bob", bob)
        self.clients.add("Charlie", charlie)

        self.send("Alice", self.alice, MsgType.CHAT_PRIVATE, receiver="Bob", payload="Tin nhắn riêng")

        self.assertTrue(any(
            item["type"] == MsgType.CHAT_PRIVATE.value
            and item["payload"] == "Tin nhắn riêng"
            for item in bob.messages()
        ))
        self.assertFalse(any(
            item["type"] == MsgType.CHAT_PRIVATE.value
            and item["payload"] == "Tin nhắn riêng"
            for item in charlie.messages()
        ))


if __name__ == "__main__":
    unittest.main()
