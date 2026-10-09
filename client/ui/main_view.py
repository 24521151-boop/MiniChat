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

        sidebar = ctk.CTkFrame(self, width=210, corner_radius=12)
        sidebar.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="Người dùng", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14, pady=(14, 4))
        ctk.CTkButton(sidebar, text="Chat chung", anchor="w", command=self.select_global).pack(fill="x", padx=10, pady=4)
        self.user_list = ctk.CTkScrollableFrame(sidebar, label_text="Chọn người để chat riêng")
        self.user_list.pack(fill="both", expand=True, padx=8, pady=(4, 10))
        self._append("Hệ thống", "Bạn đã đăng nhập. Hãy chọn phòng chat để bắt đầu.")

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

    def select_private(self, username: str):
        if username == self.username:
            return
        self.selected_user = username
        self.room_label.configure(text=f"Chat riêng với {username}")
        self._highlight_users()

    def set_users(self, names: list[str]):
        self._users = names
        for child in self.user_list.winfo_children():
            child.destroy()
        for name in names:
            if name == self.username:
                continue
            button = ctk.CTkButton(self.user_list, text=name, anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"), command=lambda n=name: self.select_private(n))
            button.pack(fill="x", padx=3, pady=2)
        if self.selected_user and self.selected_user not in names:
            self.select_global()

    def _highlight_users(self):
        # Room selection is reflected in the title; buttons remain simple and predictable.
        return

    def show_global_message(self, sender: str, text: str):
        self._append(sender or "Người dùng", text)

    def show_private_message(self, sender: str, receiver: str, text: str):
        other = receiver if sender == self.username else sender
        # Never place private content into the global room or another user's conversation.
        if self.selected_user == other:
            self._append(f"[Riêng] {sender} → {receiver}", text)
        elif sender != self.username:
            self.show_system(f"Bạn có tin nhắn riêng từ {other}. Hãy chọn người đó để xem nội dung.");

    def show_system(self, text: str):
        if text:
            self._append("Hệ thống", text)

    def _append(self, sender: str, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.configure(state="normal")
        self.messages.insert("end", f"[{timestamp}] {sender}: {text}\n")
        self.messages.see("end")
        self.messages.configure(state="disabled")
