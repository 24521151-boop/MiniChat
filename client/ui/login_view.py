import customtkinter as ctk


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login = on_login
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self, corner_radius=18)
        card.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(card, text="MiniChat", font=ctk.CTkFont(size=30, weight="bold")).pack(padx=36, pady=(28, 4))
        ctk.CTkLabel(card, text="Trò chuyện qua mạng TCP", text_color=("gray40", "gray70")).pack(padx=30, pady=(0, 22))
        self.username_entry = ctk.CTkEntry(card, width=280, height=40, placeholder_text="Nhập tên người dùng")
        self.username_entry.pack(padx=28, pady=(0, 12))
        self.username_entry.bind("<Return>", lambda _event: self.submit())
        self.login_button = ctk.CTkButton(card, text="Đăng nhập", height=40, command=self.submit)
        self.login_button.pack(fill="x", padx=28, pady=(0, 18))
        self.error_label = ctk.CTkLabel(card, text="", text_color="#e05252", wraplength=280)
        self.error_label.pack(padx=24, pady=(0, 20))
        self.username_entry.focus_set()

    def submit(self):
        username = self.username_entry.get().strip()
        if not username:
            self.show_error("Vui lòng nhập tên người dùng.")
            return
        self.login_button.configure(state="disabled", text="Đang kết nối...")
        self.error_label.configure(text="")
        self.after(10, lambda: self._call_login(username))

    def _call_login(self, username):
        try:
            self.on_login(username)
        except Exception as exc:
            self.show_error(str(exc))
            self.login_button.configure(state="normal", text="Đăng nhập")

    def show_error(self, message: str):
        self.error_label.configure(text=message)

    def set_busy(self, busy: bool):
        self.login_button.configure(state="disabled" if busy else "normal", text="Đang kết nối..." if busy else "Đăng nhập")
