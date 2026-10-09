import logging
import customtkinter as ctk
from tkinter import messagebox

from client.event_handler import EventHandler
from client.tcp_client import TCPClient
from client.ui.login_view import LoginView
from client.ui.main_view import MainView

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class MiniChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MiniChat")
        self.geometry("1000x650")
        self.minsize(760, 500)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.client: TCPClient | None = None
        self.login_view: LoginView | None = None
        self.main_view: MainView | None = None
        self.event_handler: EventHandler | None = None
        self.show_login()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_login(self, error: str = ""):
        if self.event_handler:
            self.event_handler.stop()
            self.event_handler = None
        if self.main_view:
            self.main_view.destroy()
            self.main_view = None
        if self.login_view:
            self.login_view.destroy()
        self.login_view = LoginView(self, self._login)
        self.login_view.pack(fill="both", expand=True, padx=12, pady=12)
        if error:
            self.login_view.show_error(error)

    def _login(self, username: str):
        if self.login_view:
            self.login_view.set_busy(True)
        client = TCPClient()
        success, message = client.connect_and_login(username)
        if not success:
            if self.login_view:
                self.login_view.set_busy(False)
                self.login_view.show_error(message)
            return
        self.client = client
        if self.login_view:
            self.login_view.destroy()
            self.login_view = None
        self.main_view = MainView(self, username, self._send_message, self._logout)
        self.main_view.pack(fill="both", expand=True)
        self.event_handler = EventHandler(client, self.main_view, self._connection_lost)
        self.event_handler.poll()

    def _send_message(self, recipient: str | None, text: str):
        if not self.client:
            raise ConnectionError("Chưa kết nối tới server.")
        if recipient:
            self.client.send_private(recipient, text)
        else:
            self.client.send_global(text)

    def _logout(self):
        if self.event_handler:
            self.event_handler.stop()
            self.event_handler = None
        if self.client:
            self.client.logout()
            self.client = None
        self.show_login()

    def _connection_lost(self):
        if self.client:
            self.client.close()
            self.client = None
        if self.main_view:
            self.after(1000, lambda: self.show_login("Kết nối đã kết thúc. Vui lòng đăng nhập lại."))

    def _on_close(self):
        if self.event_handler:
            self.event_handler.stop()
        if self.client:
            self.client.logout()
        self.destroy()


if __name__ == "__main__":
    MiniChatApp().mainloop()
