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


class RoomHistoryTests(unittest.TestCase):
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

    def test_room_creation_and_member_notice(self):
        bob = FakeSocket()
        self.clients.add("Bob", bob)
        charlie = FakeSocket()
        self.clients.add("Charlie", charlie)

        self.send("Alice", self.alice, MsgType.CREATE_ROOM, payload="Lớp IT005")
        self.send("Alice", self.alice, MsgType.ADD_MEMBER, receiver="Bob", payload="Lớp IT005")

        alice_types = [item["type"] for item in self.alice.messages()]
        bob_messages = bob.messages()
        charlie_messages = charlie.messages()

        self.assertIn(MsgType.ROOM_LIST.value, alice_types)
        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ALL.value
            and "Alice" in item["payload"]
            and "Lớp IT005" in item["payload"]
            for item in self.alice.messages()
        ))
        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ROOM.value
            and item["receiver"] == "Lớp IT005"
            and "Bob" in item["payload"]
            for item in bob_messages
        ))
        self.assertFalse(any(
            item["type"] == MsgType.CHAT_ROOM.value
            for item in charlie_messages
        ))

    def test_late_login_receives_public_and_room_history(self):
        self.send("Alice", self.alice, MsgType.CHAT_ALL, payload="Tin nhắn chung trước đó")
        self.send("Alice", self.alice, MsgType.CREATE_ROOM, payload="Nhóm học")
        self.send("Alice", self.alice, MsgType.ADD_MEMBER, receiver="Bob", payload="Nhóm học")
        self.send("Alice", self.alice, MsgType.CHAT_ROOM, receiver="Nhóm học", payload="Tin nhắn cũ trong phòng")

        bob = FakeSocket()
        login = Message(
            msg_type=MsgType.LOGIN,
            sender="",
            receiver="",
            payload="Bob",
        )
        self.handler.handle(bob, None, login)

        messages = bob.messages()
        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ALL.value
            and item["payload"] == "Tin nhắn chung trước đó"
            for item in messages
        ))
        self.assertTrue(any(
            item["type"] == MsgType.ROOM_LIST.value
            and "Nhóm học" in item["payload"]
            for item in messages
        ))
        self.assertTrue(any(
            item["type"] == MsgType.CHAT_ROOM.value
            and item["receiver"] == "Nhóm học"
            and item["payload"] == "Tin nhắn cũ trong phòng"
            for item in messages
        ))


if __name__ == "__main__":
    unittest.main()
