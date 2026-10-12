# MiniChat - Bài tập nhóm môn IT005

![Python](https://img.shields.io/badge/Python-3.12%20(64--bit)-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![Protocol](https://img.shields.io/badge/Network-TCP%20%2B%20UDP-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Giới thiệu

**MiniChat** là ứng dụng nhắn tin nhiều người dùng theo mô hình **Client–Server**, viết bằng Python 3.12, sử dụng socket TCP cho tin nhắn, UDP cho heartbeat/trạng thái đang nhập, JSON và giao diện CustomTkinter.

## Các tính năng chính của MiniChat

### 1. Giao tiếp bằng TCP
- **Chat chung:** Cho phép người dùng gửi và nhận tin nhắn trong cuộc trò chuyện chung.
- **Chat riêng:** Cho phép người dùng gửi và nhận tin nhắn riêng với một người dùng cụ thể.
- **Đăng nhập:** Đảm bảo việc trao đổi yêu cầu đăng nhập và phản hồi giữa máy khách và máy chủ.

### 2. Cập nhật trạng thái bằng UDP
- **Trạng thái online/offline:** Theo dõi và cập nhật trạng thái trực tuyến của người dùng thông qua cơ chế gửi gói tin định kỳ (heartbeat).
- **Trạng thái đang nhập:** Thông báo khi người dùng đang nhập tin nhắn, giúp những người tham gia cuộc trò chuyện nhận biết hoạt động của nhau.

## Công nghệ

- Python 3.12 (64-bit)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Socket TCP, UDP và threading
- JSON; mỗi thông điệp TCP kết thúc bằng ký tự xuống dòng (`\\n`) để phân tách thông điệp trên TCP stream. UDP dùng từng datagram JSON riêng.
- UDP heartbeat được xác thực bằng token phiên do Server cấp qua kết nối TCP sau khi đăng nhập thành công.

## Cấu trúc thư mục

```text
MiniChat/
├── common/
│   ├── __init__.py
│   ├── constants.py
│   └── protocol.py
├── server/
│   ├── __init__.py
│   ├── main.py
│   ├── tcp_server.py
│   ├── client_manager.py
│   ├── tcp_message_handler.py
│   ├── udp_server.py
│   └── udp_message_handler.py
├── client/
│   ├── __init__.py
│   ├── main.py
│   ├── tcp_client.py
│   ├── udp_client.py
│   ├── event_handler.py
│   └── ui/
│       ├── __init__.py
│       ├── login_view.py
│       └── main_view.py
├── tests/
│   ├── test_tcp_message_handler.py
│   └── test_udp_message_handler.py
├── .gitignore
└── README.md
```

## Cài đặt và chạy trên Windows

Yêu cầu Python 3.12. Mở Terminal hoặc PowerShell tại thư mục gốc của repository.

### 1. Cài đặt customtkinter

```powershell
pip install customtkinter
```

### 2. Khởi động Server

Mở Terminal thứ nhất tại thư mục gốc:

```powershell
python -m server.main
```

Server lắng nghe TCP tại cổng `9999` và UDP tại cổng `9998`. Giữ cửa sổ này mở trong khi sử dụng ứng dụng.

### 3. Khởi động Client

Mở Terminal thứ hai tại cùng thư mục:

```powershell
python -m client.main
```

Mở thêm cửa sổ Client bằng cách chạy lại lệnh để thử nhiều người dùng. Khi thử trên cùng máy, giữ `SERVER_IP = "127.0.0.1"` trong `common/constants.py`.

## Chạy qua mạng LAN

1. Khởi động Server trên máy chủ và xác định địa chỉ IPv4 nội bộ của máy đó.
2. Trên các máy Client, sửa `SERVER_IP` trong `common/constants.py` thành IPv4 của máy chạy Server, ví dụ `192.168.1.10`.
3. Cho phép Python hoặc cả cổng TCP `9999` và UDP `9998` qua Windows Firewall trên máy Server nếu được yêu cầu.
4. Chạy Client bằng `python -m client.main`.

Không mở các cổng này ra Internet công cộng; bản demo chưa có mã hóa TLS hay cơ chế xác thực tài khoản. UDP token giúp gắn datagram với phiên đăng nhập hiện tại, nhưng không thay thế TLS hoặc cơ chế bảo mật đầy đủ.

## Kiểm thử demo

1. Khởi động Server.
2. Mở hai hoặc ba Client với các tên khác nhau.
3. Gửi tin nhắn trong Chat chung và xác nhận các Client đang kết nối đều nhận được.
4. Đăng nhập thêm một Client sau khi đã gửi vài tin nhắn; xác nhận Client mới nhận được lịch sử Chat chung.
5. Chọn một người trong danh sách để chat riêng; xác nhận người không được chọn không nhận tin nhắn riêng.
6. Gõ vào ô tin nhắn và xác nhận Client phù hợp thấy trạng thái “đang nhập...”; dừng gõ để trạng thái tự biến mất.
7. Thử đăng nhập hai lần với cùng một tên và thử tên không hợp lệ.
8. Đóng một Client và kiểm tra danh sách người dùng được cập nhật.

## Giới hạn hiện tại

- Lịch sử Chat chung được giữ trong RAM, tối đa 500 tin nhắn trong lúc Server chạy; khởi động lại Server sẽ xóa lịch sử.
- Lịch sử Chat riêng chỉ được giữ trong bộ nhớ của cửa sổ Client hiện tại, không được đồng bộ cho người đăng nhập sau.
- UDP không bảo đảm chuyển phát datagram; trạng thái đang nhập có thể bị bỏ lỡ trong điều kiện mạng không ổn định.
- Chưa có mã hóa TLS, tài khoản/mật khẩu hoặc gửi file.
- Server dành cho bài tập và demo trong mạng tin cậy.
