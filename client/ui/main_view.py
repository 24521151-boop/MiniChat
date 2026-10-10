import customtkinter as ctk
from datetime import datetime


class MainView(ctk.CTkFrame):
    def __init__(self, master, username: str, on_send, on_logout, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username
        self.on_send = on_send
        self.on_logout = on_logout
        self.selected_user: str | None = None
        self._users: list[str] = []
        # Keep a separate message history for the global room and each private chat.
        self._global_history: list[tuple[str, str, str]] = []
        self._private_history: dict[str, list[tuple[str, str, str]]] = {}
        self._unread_private: dict[str, int] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="MiniChat", font=ctk.CTkFont(size=21, weight="bold")).grid(row=0, column=0, sticky="w", padx=18, pady=13)
        ctk.CTkLabel(header, text=f"Đăng nhập: {username}").grid(row=0, column=1, padx=12)
        ctk.CTkButton(header, text="Đăng xuất", width=95, fg_color=("gray70", "gray25"), command=self.on_logout).grid(row=0, column=2, padx=14, pady=10)

        chat = ctk.CTkFrame(self, corner_radius=12)
        chat.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)
        chat.grid_columnconfigure(0, weight=1)
        chat.grid_rowconfigure(1, weight=1)
        self.room_label = ctk.CTkLabel(chat, text="Phòng chat chung", anchor="w", font=ctk.CTkFont(size=16, weight="bold"))
        self.room_label.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        self.messages = ctk.CTkTextbox(chat, wrap="word", state="disabled")
        self.messages.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        entry_row = ctk.CTkFrame(chat, fg_color="transparent")
        entry_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 12))
        entry_row.grid_columnconfigure(0, weight=1)
        self.message_entry = ctk.CTkEntry(entry_row, height=40, placeholder_text="Nhập tin nhắn...")
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.message_entry.bind("<Return>", lambda _event: self.send_message())
        ctk.CTkButton(entry_row, text="Gửi", width=80, height=40, command=self.send_message).grid(row=0, column=1)

        sidebar = ctk.CTkFrame(self, width=230, corner_radius=12)
        sidebar.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="Người dùng", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14, pady=(14, 4))
        ctk.CTkButton(sidebar, text="Chat chung", anchor="w", command=self.select_global).pack(fill="x", padx=10, pady=4)
        self.user_list = ctk.CTkScrollableFrame(sidebar, label_text="Chọn người để chat riêng", height=220)
        self.user_list.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Keep system notices in a dedicated sidebar area so changing chat rooms
        # never hides them or mixes them into the conversation history.
        notification_panel = ctk.CTkFrame(sidebar, corner_radius=10)
        notification_panel.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(
            notification_panel,
            text="🔔 Thông báo",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 4))
        self.notifications = ctk.CTkTextbox(
            notification_panel,
            height=115,
            wrap="word",
            state="disabled",
        )
        self.notifications.pack(fill="x", padx=8, pady=(0, 8))
        self.show_notification("Bạn đã đăng nhập. Hãy chọn phòng chat để bắt đầu.")

    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        try:
            self.on_send(self.selected_user, text)
            self.message_entry.delete(0, "end")
        except Exception as exc:
            self.show_system(f"Không gửi được tin nhắn: {exc}")

    def select_global(self):
        self.selected_user = None
        self.room_label.configure(text="Phòng chat chung")
        self._highlight_users()
        self._render_history(self._global_history)

    def select_private(self, username: str):
        if username == self.username:
            return
        self.selected_user = username
        self._unread_private[username] = 0
        self.room_label.configure(text=f"Chat riêng với {username}")
        self._highlight_users()
        self._render_history(self._private_history.setdefault(username, []))
        self._refresh_user_buttons()

    def set_users(self, names: list[str]):
        self._users = names
        for child in self.user_list.winfo_children():
            child.destroy()
        for name in names:
            if name == self.username:
                continue
            unread = self._unread_private.get(name, 0)
            label = f"{name}  ({unread} mới)" if unread else name
            button = ctk.CTkButton(
                self.user_list,
                text=label,
                anchor="w",
                fg_color=("gray80", "gray25") if name == self.selected_user else "transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray30"),
                command=lambda n=name: self.select_private(n),
            )
            button.pack(fill="x", padx=3, pady=2)
        if self.selected_user and self.selected_user not in names:
            self.select_global()

    def _refresh_user_buttons(self):
        # Rebuild labels so unread counters and the selected conversation stay in sync.
        self.set_users(self._users)

    def _highlight_users(self):
        self._refresh_user_buttons()

    def show_global_message(self, sender: str, text: str):
        entry = (datetime.now().strftime("%H:%M:%S"), sender or "Người dùng", text)
        self._global_history.append(entry)
        if self.selected_user is None:
            self._append_entry(entry)

    def show_private_message(self, sender: str, receiver: str, text: str):
        # The server sends a copy to both participants. Save it even if this chat
        # is not currently selected, so switching conversations never loses messages.
        other = receiver if sender == self.username else sender
        if not other or other == self.username:
            return
        entry = (datetime.now().strftime("%H:%M:%S"), sender or "Người dùng", text)
        history = self._private_history.setdefault(other, [])
        history.append(entry)

        if self.selected_user == other:
            self._append_entry(entry, private=True)
        elif sender != self.username:
            self._unread_private[other] = self._unread_private.get(other, 0) + 1
            self._refresh_user_buttons()

    def show_notification(self, text: str):
        """Append a system notice to the persistent sidebar notification panel."""
        if not text:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.notifications.configure(state="normal")
        self.notifications.insert("end", f"[{timestamp}] {text}\n")
        self.notifications.see("end")
        self.notifications.configure(state="disabled")

    def show_system(self, text: str):
        # Keep the existing method name for callers elsewhere in the client.
        self.show_notification(text)

    def _render_history(self, history: list[tuple[str, str, str]]):
        self.messages.configure(state="normal")
        self.messages.delete("1.0", "end")
        for entry in history:
            self._insert_entry(entry, private=self.selected_user is not None)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _append_entry(self, entry: tuple[str, str, str], private: bool = False):
        self.messages.configure(state="normal")
        self._insert_entry(entry, private=private)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _insert_entry(self, entry: tuple[str, str, str], private: bool = False):
        timestamp, sender, text = entry
        prefix = "[Riêng] " if private else ""
        if private:
            other = self.selected_user or ""
            receiver = other if sender == self.username else self.username
            sender_label = f"{prefix}{sender} → {receiver}"
        else:
            sender_label = sender
        self.messages.insert("end", f"[{timestamp}] {sender_label}: {text}\n")

    def _append(self, sender: str, text: str):
        # Preserve the helper for any existing internal callers, but route system
        # output to the notification panel rather than the selected chat history.
        if sender == "Hệ thống":
            self.show_notification(text)
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.configure(state="normal")
        self.messages.insert("end", f"[{timestamp}] {sender}: {text}\n")
        self.messages.see("end")
        self.messages.configure(state="disabled")
