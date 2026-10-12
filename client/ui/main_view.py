import customtkinter as ctk
from datetime import datetime


class MainView(ctk.CTkFrame):
    def __init__(self, master, username: str, on_send, on_logout, on_typing=None, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username
        self.on_send = on_send
        self.on_logout = on_logout
        self.on_typing = on_typing or (lambda _recipient, _typing: None)
        self.selected_user: str | None = None
        self._users: list[str] = []
        self._online_users: set[str] = set()
        self._global_history: list[tuple[str, str, str]] = []
        self._private_history: dict[str, list[tuple[str, str, str]]] = {}
        self._unread_private: dict[str, int] = {}
        self._typing_after_id = None
        self._typing_active = False
        self._typing_display_after_id = None
        self._typing_display_text = ""

        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1, minsize=250)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="MiniChat", font=ctk.CTkFont(size=21, weight="bold")).grid(row=0, column=0, sticky="w", padx=18, pady=13)
        ctk.CTkLabel(header, text=f"Đăng nhập: {username}").grid(row=0, column=1, padx=12)
        ctk.CTkButton(header, text="Đăng xuất", width=95, fg_color=("gray70", "gray25"), command=self.on_logout).grid(row=0, column=2, padx=14, pady=10)

        chat = ctk.CTkFrame(self, corner_radius=12)
        chat.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)
        chat.grid_columnconfigure(0, weight=1)
        chat.grid_rowconfigure(2, weight=1)
        self.chat_title = ctk.CTkLabel(chat, text="Chat chung", anchor="w", font=ctk.CTkFont(size=16, weight="bold"))
        self.chat_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        self.typing_label = ctk.CTkLabel(chat, text="", anchor="w", text_color=("gray45", "gray65"))
        self.typing_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 2))
        self.messages = ctk.CTkTextbox(chat, wrap="word", state="disabled")
        self.messages.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        entry_row = ctk.CTkFrame(chat, fg_color="transparent")
        entry_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 12))
        entry_row.grid_columnconfigure(0, weight=1)
        self.message_entry = ctk.CTkEntry(entry_row, height=40, placeholder_text="Nhập tin nhắn...")
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.message_entry.bind("<Return>", lambda _event: self.send_message())
        self.message_entry.bind("<KeyRelease>", self._on_message_key_release)
        ctk.CTkButton(entry_row, text="Gửi", width=80, height=40, command=self.send_message).grid(row=0, column=1)

        sidebar = ctk.CTkFrame(self, width=280, corner_radius=12)
        sidebar.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=3)
        sidebar.grid_rowconfigure(5, weight=2)

        ctk.CTkLabel(sidebar, text="Trò chuyện", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 3))
        ctk.CTkButton(sidebar, text="Chat chung", anchor="w", command=self.select_global).grid(row=1, column=0, sticky="ew", padx=8, pady=3)
        ctk.CTkLabel(sidebar, text="Người dùng", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, sticky="w", padx=12, pady=(5, 2))
        self.user_list = ctk.CTkScrollableFrame(sidebar, height=150, label_text="Chọn người để chat riêng")
        self.user_list.grid(row=3, column=0, sticky="nsew", padx=8, pady=(2, 5))
        ctk.CTkLabel(sidebar, text="Thông báo hệ thống", font=ctk.CTkFont(size=14, weight="bold")).grid(row=4, column=0, sticky="w", padx=12, pady=(5, 2))
        self.notifications = ctk.CTkTextbox(sidebar, height=130, wrap="word", state="disabled")
        self.notifications.grid(row=5, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.show_system("Bạn đã đăng nhập.")

    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        self._set_local_typing(False)
        try:
            self.on_send(self.selected_user, text)
            self.message_entry.delete(0, "end")
        except Exception as exc:
            self.show_system(f"Không gửi được tin nhắn: {exc}")

    def _on_message_key_release(self, _event=None):
        if self.message_entry.get().strip():
            self._typing_active = True
            self.on_typing(self.selected_user or "", True)
            if self._typing_after_id is not None:
                try:
                    self.after_cancel(self._typing_after_id)
                except Exception:
                    pass
            self._typing_after_id = self.after(1500, lambda: self._set_local_typing(False))
        else:
            self._set_local_typing(False)

    def _set_local_typing(self, typing: bool):
        if self._typing_after_id is not None:
            try:
                self.after_cancel(self._typing_after_id)
            except Exception:
                pass
            self._typing_after_id = None
        if self._typing_active != typing:
            self._typing_active = typing
            self.on_typing(self.selected_user or "", typing)

    def select_global(self):
        self._set_local_typing(False)
        self.selected_user = None
        self._clear_typing_display()
        self.chat_title.configure(text="Chat chung")
        self._refresh_user_buttons()
        self._render_history(self._global_history)

    def select_private(self, username: str):
        if username == self.username or username not in self._online_users:
            return
        self._set_local_typing(False)
        self.selected_user = username
        self._clear_typing_display()
        self._unread_private[username] = 0
        self.chat_title.configure(text=f"Chat riêng với {username}")
        self._refresh_user_buttons()
        self._render_history(self._private_history.setdefault(username, []), private=True)

    def set_users(self, known_names: list[str], online_names: list[str] | None = None):
        online_names = known_names if online_names is None else online_names
        self._users = sorted(set(known_names), key=str.casefold)
        self._online_users = set(online_names)
        for child in self.user_list.winfo_children():
            child.destroy()
        for name in self._users:
            if name == self.username:
                continue
            online = name in self._online_users
            unread = self._unread_private.get(name, 0)
            status = "●" if online else "○"
            label = f"{status}  {name}"
            if unread:
                label += f"  ({unread} mới)"
            button = ctk.CTkButton(
                self.user_list,
                text=label,
                anchor="w",
                fg_color=("gray80", "gray25") if name == self.selected_user else "transparent",
                text_color=(("green", "lightgreen") if online else ("gray55", "gray60")),
                hover_color=("gray85", "gray30"),
                state="normal" if online else "disabled",
                command=lambda n=name: self.select_private(n),
            )
            button.pack(fill="x", padx=3, pady=2)
        if self.selected_user and self.selected_user not in self._online_users:
            self.select_global()

    def show_global_message(self, sender: str, text: str):
        entry = (datetime.now().strftime("%H:%M:%S"), sender or "Người dùng", text)
        self._global_history.append(entry)
        if self.selected_user is None:
            self._append_entry(entry)

    def show_private_message(self, sender: str, receiver: str, text: str):
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

    def show_typing(self, sender: str, receiver: str, typing: bool):
        if not sender or sender == self.username:
            return
        relevant = (not receiver and self.selected_user is None) or (receiver == self.username and self.selected_user == sender)
        if not relevant:
            return
        if self._typing_display_after_id is not None:
            try:
                self.after_cancel(self._typing_display_after_id)
            except Exception:
                pass
            self._typing_display_after_id = None
        if typing:
            text = f"{sender} đang nhập..."
            self._typing_display_text = text
            self.typing_label.configure(text=text)
            self._typing_display_after_id = self.after(2500, self._clear_typing_display)
        elif self._typing_display_text.startswith(f"{sender} đang nhập"):
            self._clear_typing_display()

    def _clear_typing_display(self):
        if self._typing_display_after_id is not None:
            try:
                self.after_cancel(self._typing_display_after_id)
            except Exception:
                pass
            self._typing_display_after_id = None
        self._typing_display_text = ""
        self.typing_label.configure(text="")

    def show_system(self, text: str):
        if not text:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {text}"
        self.notifications.configure(state="normal")
        self.notifications.insert("end", entry + "\n")
        self.notifications.see("end")
        self.notifications.configure(state="disabled")

    def _refresh_user_buttons(self):
        self.set_users(self._users, list(self._online_users))

    def _render_history(self, history: list[tuple[str, str, str]], private: bool = False):
        self.messages.configure(state="normal")
        self.messages.delete("1.0", "end")
        for entry in history:
            self._insert_entry(entry, private=private)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _append_entry(self, entry: tuple[str, str, str], private: bool = False):
        self.messages.configure(state="normal")
        self._insert_entry(entry, private=private)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _insert_entry(self, entry: tuple[str, str, str], private: bool = False):
        timestamp, sender, text = entry
        if private:
            other = self.selected_user or ""
            receiver = other if sender == self.username else self.username
            sender_label = f"[Riêng] {sender} → {receiver}"
        else:
            sender_label = sender
        self.messages.insert("end", f"[{timestamp}] {sender_label}: {text}\n")
