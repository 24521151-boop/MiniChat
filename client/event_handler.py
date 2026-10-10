import json
import logging
from typing import Any, Callable

from common.protocol import MsgType
from client.tcp_client import TCPClient

logger = logging.getLogger(__name__)

class EventHandler:
    """Routes queued network events to the GUI on Tk's main thread."""

    def __init__(self, client: TCPClient, view: Any, on_disconnected: Callable[[], None]) -> None:
        self.client = client
        self.view = view
        self.on_disconnected = on_disconnected
        self._running = True

    def poll(self) -> None:
        if not self._running:
            return
        while True:
            try:
                item = self.client.incoming.get_nowait()
            except Exception:
                break
            self._dispatch(item)
        if self._running:
            try:
                self.view.after(100, self.poll)
            except Exception:
                self._running = False

    def stop(self) -> None:
        self._running = False

    def _show_notice(self, message: str) -> None:
        """Send system notices to the dedicated panel, with backward compatibility."""
        show_notification = getattr(self.view, "show_notification", None)
        if callable(show_notification):
            show_notification(message)
        else:
            self.view.show_system(message)

    def _dispatch(self, item: dict[str, Any]) -> None:
        msg_type = item.get("type", "")
        if msg_type == "_DISCONNECTED":
            self._show_notice("Đã ngắt kết nối tới server.")
            self.on_disconnected()
            self.stop()
            return
        if msg_type == MsgType.USER_LIST.value:
            try:
                names = json.loads(item.get("payload", "[]"))
                if isinstance(names, list) and all(isinstance(name, str) for name in names):
                    self.view.set_users(names)
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
            self._show_notice(str(payload.get("message", "")))
