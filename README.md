# MiniChat - Bài tập nhóm 4 môn IT005

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 Giới thiệu
**MiniChat** là một ứng dụng chat cơ bản được phát triển bằng ngôn ngữ Python, phục vụ cho bài tập nhóm môn IT005. Ứng dụng cung cấp giao diện đồ họa thân thiện (GUI) và hỗ trợ các tính năng nhắn tin, gửi file và quản lý trạng thái người dùng thông qua mạng LAN.

## ✨ Tính năng chính
- **Đăng nhập:** Người dùng đăng nhập vào hệ thống bằng tên (Username) thông qua giao thức TCP.
- **Chat nhóm:** Tạo phòng mới, tham gia phòng và trò chuyện với nhiều người (TCP).
- **Chat riêng:** Nhắn tin trực tiếp 1-1 giữa hai người dùng.
- **Gửi file:** Hỗ trợ gửi file tài liệu trong cả chat nhóm và chat riêng (TCP).
- **Trạng thái:** Hiển thị trạng thái Online/Offline và trạng thái "đang nhập" (typing) thời gian thực (UDP).
- **Giao diện:** Sử dụng CustomTkinter mang lại giao diện hiện đại, dễ sử dụng.

## 🛠 Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.x
- **Giao diện (GUI):** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Giao thức mạng:**
  - **TCP:** Dùng cho các tác vụ yêu cầu độ tin cậy cao (Đăng nhập, Gửi tin nhắn, Truyền file).
  - **UDP:** Dùng cho các tác vụ yêu cầu tốc độ nhanh, không cần đảm bảo 100% (Heartbeat, Trạng thái online/offline, Typing indicator).

## 📂 Cấu trúc thư mục
```text
MiniChat/
├── client/                     # Mã nguồn phía người dùng
│   ├── main.py                 # Khởi chạy ứng dụng client
│   ├── tcp_client.py           # Kết nối TCP, gửi/nhận tin nhắn và file
│   ├── udp_client.py           # Gửi heartbeat, trạng thái đăng nhập
│   ├── event_handler.py        # Xử lý thao tác, kết nối UI với mạng
│   └── ui/                     # Chứa các giao diện (Views)
│       ├── login_view.py       # Giao diện đăng nhập
│       ├── main_view.py        # Giao diện chính (danh sách user, phòng)
│       ├── room_view.py        # Giao diện chat nhóm
│       ├── private_chat_view.py# Giao diện chat riêng
│       └── file_view.py        # Giao diện chọn, gửi, nhận file
├── server/                     # Mã nguồn phía máy chủ
│   ├── main.py                 # Khởi chạy server TCP và UDP
│   ├── tcp_server.py           # Lắng nghe và chấp nhận kết nối TCP
│   ├── udp_server.py           # Nhận và gửi datagram UDP
│   ├── client_manager.py       # Quản lý client đang kết nối
│   ├── room_manager.py         # Tạo phòng, quản lý thành viên
│   ├── message_handler.py      # Xử lý, định tuyến tin nhắn
│   ├── file_handler.py         # Tiếp nhận, lưu trữ, chuyển tiếp file
│   └── presence_manager.py     # Quản lý trạng thái online/offline
├── common/                     # Quy ước dùng chung
│   ├── protocol.py             # Định dạng thông điệp, cấu trúc gói tin
│   └── constants.py            # Hằng số (cổng TCP/UDP, giới hạn file)
├── data/                       # Thư mục lưu trữ dữ liệu
│   └── files/                  # Lưu file tài liệu được gửi qua chat
└── README.md
