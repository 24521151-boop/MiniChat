# MiniChat - Bài tập nhóm môn IT005

![Python](https://img.shields.io/badge/Python-3.12%20(64--bit)-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![Protocol](https://img.shields.io/badge/Network-TCP-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 Giới thiệu

**MiniChat** là ứng dụng nhắn tin nhiều người dùng được xây dựng bằng **Python 3.12**, phục vụ bài tập nhóm môn IT005. Ứng dụng sử dụng mô hình **Client–Server**, giao tiếp qua TCP và cung cấp giao diện đồ họa bằng **CustomTkinter**.

## ✨ Tính năng mục tiêu

- **Đăng nhập:** Người dùng kết nối đến Server bằng tên người dùng.
- **Chat chung:** Các Client gửi và nhận tin nhắn trong phòng chat chung.
- **Chat riêng:** Người dùng chọn một người để trao đổi tin nhắn 1-1.
- **Danh sách người dùng:** Hiển thị danh sách tài khoản mà Server đang quản lý; không triển khai cơ chế theo dõi trạng thái online/offline riêng.
- **Giao diện đồ họa:** Xây dựng bằng CustomTkinter.

> Phạm vi hiện tại không bao gồm gửi file hoặc cập nhật trạng thái online/offline bằng UDP heartbeat.

## 🛠 Công nghệ sử dụng

- **Ngôn ngữ:** Python 3.12 (64-bit)
- **Giao diện:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Mạng:** Socket TCP
- **Đa luồng:** `threading` để xử lý kết nối và nhận dữ liệu mà không làm treo giao diện.
- **Trao đổi thông điệp:** JSON, mỗi thông điệp kết thúc bằng ký tự xuống dòng (`\n`) để phân tách dữ liệu trên luồng TCP.

## 📂 Cấu trúc thư mục

### Cấu trúc hiện có

```text
MiniChat/
├── common/
│   ├── constants.py    # Cấu hình dùng chung: địa chỉ Server, cổng TCP, buffer, encoding
│   └── protocol.py     # Định nghĩa loại thông điệp và hàm đóng gói/phân tích JSON
├── .gitignore
└── README.md
```

### Cấu trúc dự kiến khi hoàn thiện

```text
MiniChat/
├── common/                     # Thành phần dùng chung giữa Client và Server
│   ├── constants.py            # Cấu hình mạng và mã hóa
│   └── protocol.py             # Định dạng thông điệp: LOGIN, LOGOUT, USER_LIST,
│                               # CHAT_ALL, CHAT_PRIVATE, SYSTEM
│
├── server/                     # Xử lý kết nối và định tuyến tin nhắn
│   ├── main.py                 # Điểm khởi chạy Server
│   ├── tcp_server.py           # Lắng nghe kết nối TCP và nhận dữ liệu từ Client
│   ├── client_manager.py       # Quản lý các Client đang kết nối
│   └── message_handler.py      # Xử lý đăng nhập, chat chung và chat riêng
│
├── client/                     # Kết nối mạng và giao diện người dùng
│   ├── main.py                 # Điểm khởi chạy ứng dụng Client
│   ├── tcp_client.py           # Kết nối Server và nhận/gửi thông điệp TCP
│   ├── event_handler.py        # Kết nối sự kiện giao diện với xử lý mạng
│   └── ui/
│       ├── login_view.py       # Màn hình đăng nhập
│       └── main_view.py        # Màn hình chat và danh sách người dùng
│
├── .gitignore
└── README.md
```

> **Lưu ý:** Phần “Cấu trúc dự kiến” là thiết kế mục tiêu, không có nghĩa các thư mục và tệp đó đã được tạo trong repository. Khi cấu trúc mã nguồn thay đổi, hãy cập nhật lại sơ đồ này để README luôn phản ánh đúng dự án.
