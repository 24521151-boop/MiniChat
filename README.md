# MiniChat - Bài tập nhóm môn IT005

![Python](https://img.shields.io/badge/Python-3.12%20(64--bit)-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![Protocol](https://img.shields.io/badge/Network-TCP%20%2F%20UDP-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 Giới thiệu
**MiniChat** là một ứng dụng chat cơ bản được phát triển bằng ngôn ngữ **Python 3.12 (64-bit)**, phục vụ cho bài tập nhóm môn IT005. Ứng dụng cung cấp giao diện đồ họa hiện đại (GUI) và hỗ trợ các tính năng nhắn tin, quản lý trạng thái người dùng thông qua mạng LAN.

Dự án tập trung vào việc ứng dụng lập trình mạng với **Socket (TCP/UDP)**, xử lý đa luồng (**Threading**) và tích hợp với giao diện đồ họa **CustomTkinter**.

## ✨ Tính năng chính
- **Đăng nhập:** Người dùng đăng nhập vào hệ thống bằng tên (Username) thông qua giao thức TCP.
- **Chat chung (Global Chat):** Mọi người dùng đang online đều có thể gửi và nhận tin nhắn trong một khung chat chung.
- **Chat riêng (Private Chat):** Người dùng có thể chọn một người cụ thể trong danh sách để trò chuyện 1-1.
- **Trạng thái Online/Offline:** Hệ thống tự động cập nhật và hiển thị trạng thái hoạt động của người dùng theo thời gian thực (sử dụng UDP Heartbeat).
- **Giao diện:** Sử dụng CustomTkinter mang lại giao diện Dark/Light mode hiện đại, dễ sử dụng.

## 🛠 Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.12 (64-bit)
- **Giao diện (GUI):** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Giao thức mạng:**
  - **TCP:** Dùng cho các tác vụ yêu cầu độ tin cậy cao (Đăng nhập, Gửi tin nhắn chung/riêng).
  - **UDP:** Dùng cho các tác vụ yêu cầu tốc độ nhanh, không cần đảm bảo 100% (Heartbeat, Trạng thái online/offline).
- **Xử lý đa luồng:** Sử dụng `threading` và `queue.Queue` để tách biệt luồng nhận dữ liệu mạng (`socket.recv()`) và luồng cập nhật giao diện, giúp GUI không bị đơ (freeze).

## 📂 Cấu trúc thư mục
```text
MiniChat/
│
├── common/                         # Quy ước dùng chung giữa Client và Server
│   ├── constants.py                # Chứa các hằng số: TCP_PORT, UDP_PORT, BUFFER_SIZE, HEARTBEAT_INTERVAL
│   └── protocol.py                 # Định nghĩa cấu trúc gói tin (LOGIN, CHAT_ALL, CHAT_PRIVATE, USER_LIST, HEARTBEAT)
│
├── server/                         # Máy chủ trung tâm điều phối
│   ├── main.py                     # Khởi tạo và chạy song song 2 luồng (Thread) cho TCP và UDP Server
│   ├── tcp_server.py               # Lắng nghe kết nối TCP, accept() và tạo luồng riêng cho từng Client
│   ├── udp_server.py               # Lắng nghe gói tin UDP (chủ yếu là tín hiệu Heartbeat từ Client)
│   ├── client_manager.py           # Quản lý danh sách user online: {username: tcp_socket}.
│   ├── message_handler.py          # Xử lý logic: Định tuyến tin nhắn Chat chung và Chat riêng.
│   └── presence_manager.py         # Quản lý trạng thái Online/Offline dựa trên Heartbeat.
│
├── client/                         # Máy khách (Xử lý mạng + Giao diện)
│   ├── main.py                     # Khởi chạy ứng dụng CustomTkinter.
│   ├── tcp_client.py               # Kết nối TCP, luồng riêng nhận dữ liệu qua socket.recv().
│   ├── udp_client.py               # Luồng riêng gửi gói HEARTBEAT qua UDP mỗi 5 giây.
│   ├── event_handler.py            # Cầu nối giữa UI và Mạng (Sử dụng Queue).
│   └── ui/                         # Giao diện CustomTkinter
│       ├── login_view.py           # Form nhập tên người dùng.
│       └── main_view.py            # Màn hình chính: Danh sách User và Khung Chat.
│
└── README.md
