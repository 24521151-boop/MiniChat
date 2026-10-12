import json
import logging
from queue import Empty
from typing import Any, Callable

from common.protocol import MsgType
from client.tcp_client import TCPClient
from client.udp_client import UDPClient

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(
        self,
        client: TCPClient,
        view: Any,
        on_disconnected: Callable[[], None],
        udp_client: UDPClient | None = None,
    ) -> None:
        self.client = client
        self.udp_client = udp_client
        self.view = view
        self.on_disconnected = on_disconnected
        self._running = True

    def poll(self) -> None:
        if not self._running:
            return
        while True:
            try:
                item = self.client.incoming.get_nowait()
            except Empty:
                break
            self._dispatch(item)
        if self.udp_client is not None:
            while True:
                try:
                    item = self.udp_client.incoming.get_nowait()
                except Empty:
                    break
                if item.get("type") == "TYPING":
                    self.view.show_typing(
                        str(item.get("sender", "")),
                        str(item.get("receiver", "")),
                        item.get("typing") is True,
                    )
        if self._running:
            try:
                self.view.after(100, self.poll)
            except Exception:
                self._running = False

    def stop(self) -> None:
        self._running = False

    def _dispatch(self, item: dict[str, Any]) -> None:
        msg_type = item.get("type", "")
        if msg_type == "_DISCONNECTED":
            self.view.show_system("Đã ngắt kết nối tới server.")
            self.on_disconnected()
            self.stop()
            return
        if msg_type == MsgType.USER_LIST.value:
            try:
                users = json.loads(item.get("payload", "[]"))
                if isinstance(users, list) and all(isinstance(name, str) for name in users):
                    self.view.set_users(users, users)
                elif (
                    isinstance(users, dict)
                    and isinstance(users.get("known"), list)
                    and isinstance(users.get("online"), list)
                    and all(isinstance(name, str) for name in users["known"])
                    and all(isinstance(name, str) for name in users["online"])
                    and set(users["online"]).issubset(users["known"])
                ):
                    self.view.set_users(users["known"], users["online"])
                else:
                    logger.warning("Invalid user list received")
            except json.JSONDecodeError:
                logger.warning("Invalid user list received")
            return
        if msg_type == MsgType.CHAT_ALL.value:
            self.view.show_global_message(item.get("sender", ""), item.get("payload", ""))
            return
        if msg_type == MsgType.CHAT_PRIVATE.value:
            self.view.show_private_message(item.get("sender", ""), item.get("receiver", ""), item.get("payload", ""))
            return
        if msg_type == MsgType.SYSTEM.value:
            try:
                payload = json.loads(item.get("payload", "{}"))
            except json.JSONDecodeError:
                payload = {"event": "NOTICE", "message": item.get("payload", "")}
            self.view.show_system(str(payload.get("message", "")))
