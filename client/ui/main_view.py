import customtkinter as ctk
from datetime import datetime


class MainView(ctk.CTkFrame):
    def __init__(self, master, username: str, on_send, on_logout, on_create_room, on_add_member, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username
        self.on_send = on_send
        self.on_logout = on_logout
        self.on_create_room = on_create_room
        self.on_add_member = on_add_member
        self.selected_user: str | None = None
        self.selected_room: str | None = None
        self._users: list[str] = []
        self._rooms: list[dict] = []
        self._global_history: list[tuple[str, str, str]] = []
        self._private_history: dict[str, list[tuple[str, str, str]]] = {}
        self._room_history: dict[str, list[tuple[str, str, str]]] = {}
        self._unread_private: dict[str, int] = {}

        self.grid_columnconfigure(0, weight=1)
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

        sidebar = ctk.CTkFrame(self, width=280, corner_radius=12)
        sidebar.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=2)
        sidebar.grid_rowconfigure(5, weight=2)
        sidebar.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(sidebar, text="Trò chuyện", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 3))
        ctk.CTkButton(sidebar, text="Chat chung", anchor="w", command=self.select_global).grid(row=1, column=0, sticky="ew", padx=8, pady=3)
        ctk.CTkLabel(sidebar, text="Phòng chat", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, sticky="w", padx=12, pady=(5, 2))
        self.room_list = ctk.CTkScrollableFrame(sidebar, height=90)
        self.room_list.grid(row=3, column=0, sticky="nsew", padx=8, pady=(2, 5))
        ctk.CTkLabel(sidebar, text="Người dùng", font=ctk.CTkFont(size=14, weight="bold")).grid(row=4, column=0, sticky="w", padx=12, pady=(3, 2))
        self.user_list = ctk.CTkScrollableFrame(sidebar, height=85, label_text="Chat riêng")
        self.user_list.grid(row=5, column=0, sticky="nsew", padx=8, pady=(2, 5))

        create_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        create_row.grid(row=6, column=0, sticky="ew", padx=8, pady=3)
        create_row.grid_columnconfigure(0, weight=1)
        self.room_entry = ctk.CTkEntry(create_row, height=32, placeholder_text="Tên phòng mới")
        self.room_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.room_entry.bind("<Return>", lambda _event: self.create_room())
        ctk.CTkButton(create_row, text="Tạo", width=55, height=32, command=self.create_room).grid(row=0, column=1)

        member_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        member_row.grid(row=7, column=0, sticky="ew", padx=8, pady=3)
        member_row.grid_columnconfigure(0, weight=1)
        self.member_entry = ctk.CTkEntry(member_row, height=32, placeholder_text="Tên đăng nhập")
        self.member_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.member_entry.bind("<Return>", lambda _event: self.add_member())
        ctk.CTkButton(member_row, text="Thêm", width=55, height=32, command=self.add_member).grid(row=0, column=1)

        ctk.CTkLabel(sidebar, text="Thông báo", font=ctk.CTkFont(size=14, weight="bold")).grid(row=8, column=0, sticky="w", padx=12, pady=(4, 2))
        self.notifications = ctk.CTkTextbox(sidebar, height=65, wrap="word", state="disabled")
        self.notifications.grid(row=9, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self._notification_history: list[str] = []
        self.show_system("Bạn đã đăng nhập.")

    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        target = f"room:{self.selected_room}" if self.selected_room else self.selected_user
        try:
            self.on_send(target, text)
            self.message_entry.delete(0, "end")
        except Exception as exc:
            self.show_system(f"Không gửi được tin nhắn: {exc}")

    def create_room(self):
        name = self.room_entry.get().strip()
        if not name:
            self.show_system("Hãy nhập tên phòng trước khi tạo.")
            return
        try:
            self.on_create_room(name)
            self.room_entry.delete(0, "end")
        except Exception as exc:
            self.show_system(f"Không tạo được phòng: {exc}")

    def add_member(self):
        member = self.member_entry.get().strip()
        if not self.selected_room:
            self.show_system("Hãy chọn phòng bạn đã tạo trước khi thêm thành viên.")
            return
        if not member:
            self.show_system("Hãy nhập tên đăng nhập cần thêm.")
            return
        try:
            self.on_add_member(self.selected_room, member)
            self.member_entry.delete(0, "end")
        except Exception as exc:
            self.show_system(f"Không thêm được thành viên: {exc}")

    def select_global(self):
        self.selected_user = None
        self.selected_room = None
        self.room_label.configure(text="Phòng chat chung")
        self._highlight_users()
        self._highlight_rooms()
        self._render_history(self._global_history)

    def select_private(self, username: str):
        if username == self.username:
            return
        self.selected_user = username
        self.selected_room = None
        self._unread_private[username] = 0
        self.room_label.configure(text=f"Chat riêng với {username}")
        self._highlight_users()
        self._highlight_rooms()
        self._render_history(self._private_history.setdefault(username, []), private=True)

    def select_room(self, room_name: str):
        self.selected_room = room_name
        self.selected_user = None
        self.room_label.configure(text=f"Phòng: {room_name}")
        self._highlight_users()
        self._highlight_rooms()
        self._render_history(self._room_history.setdefault(room_name, []), room=True)

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

    def set_rooms(self, rooms: list[dict]):
        self._rooms = [room for room in rooms if isinstance(room, dict) and isinstance(room.get("name"), str)]
        room_names = {room["name"] for room in self._rooms}
        for child in self.room_list.winfo_children():
            child.destroy()
        for room in self._rooms:
            name = room["name"]
            owner = room.get("owner", "")
            label = f"{name}  ·  {len(room.get('members', []))}"
            button = ctk.CTkButton(
                self.room_list,
                text=label,
                anchor="w",
                fg_color=("gray80", "gray25") if name == self.selected_room else "transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray30"),
                command=lambda n=name: self.select_room(n),
            )
            button.pack(fill="x", padx=3, pady=2)
        if self.selected_room and self.selected_room not in room_names:
            self.select_global()

    def _refresh_user_buttons(self):
        self.set_users(self._users)

    def _highlight_users(self):
        self._refresh_user_buttons()

    def _highlight_rooms(self):
        self.set_rooms(self._rooms)

    def show_global_message(self, sender: str, text: str):
        entry = (datetime.now().strftime("%H:%M:%S"), sender or "Người dùng", text)
        self._global_history.append(entry)
        if self.selected_user is None and self.selected_room is None:
            self._append_entry(entry)

    def show_room_message(self, room_name: str, sender: str, text: str):
        entry = (datetime.now().strftime("%H:%M:%S"), sender or "Người dùng", text)
        history = self._room_history.setdefault(room_name, [])
        history.append(entry)
        if self.selected_room == room_name:
            self._append_entry(entry, room=True)

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

    def show_system(self, text: str):
        if not text:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {text}"
        self._notification_history.append(entry)
        self._notification_history = self._notification_history[-100:]
        self.notifications.configure(state="normal")
        self.notifications.insert("end", entry + "\n")
        self.notifications.see("end")
        self.notifications.configure(state="disabled")

    def _render_history(self, history: list[tuple[str, str, str]], private: bool = False, room: bool = False):
        self.messages.configure(state="normal")
        self.messages.delete("1.0", "end")
        for entry in history:
            self._insert_entry(entry, private=private, room=room)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _append_entry(self, entry: tuple[str, str, str], private: bool = False, room: bool = False):
        self.messages.configure(state="normal")
        self._insert_entry(entry, private=private, room=room)
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _insert_entry(self, entry: tuple[str, str, str], private: bool = False, room: bool = False):
        timestamp, sender, text = entry
        if private:
            other = self.selected_user or ""
            receiver = other if sender == self.username else self.username
            sender_label = f"[Riêng] {sender} → {receiver}"
        elif room and sender != "Hệ thống":
            sender_label = sender
        else:
            sender_label = sender
        self.messages.insert("end", f"[{timestamp}] {sender_label}: {text}\n")
