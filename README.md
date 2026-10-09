# MiniChat - Bài tập nhóm môn IT005

![Python](https://img.shields.io/badge/Python-3.12%20(64--bit)-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![Protocol](https://img.shields.io/badge/Network-TCP-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Giới thiệu

**MiniChat** là ứng dụng nhắn tin nhiều người dùng theo mô hình **Client–Server**, viết bằng Python 3.12, sử dụng socket TCP, giao thức JSON và giao diện CustomTkinter.

## Tính năng

- Đăng nhập bằng tên người dùng; từ chối tên trống, không hợp lệ hoặc đang được sử dụng.
- Chat chung với những người đang kết nối.
- Chat riêng 1-1.
- Danh sách người dùng do Server quản lý.
- Giao diện đồ họa có thông báo hệ thống và xử lý nhận tin nhắn trên luồng riêng.
- Không sử dụng UDP, không hỗ trợ gửi file và không có hệ thống trạng thái online/offline riêng biệt.

## Công nghệ

- Python 3.12 (64-bit)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Socket TCP và threading
- JSON; mỗi thông điệp kết thúc bằng ký tự xuống dòng (`\n`) để phân tách thông điệp trên TCP stream.

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
│   └── message_handler.py
├── client/
│   ├── __init__.py
│   ├── main.py
│   ├── tcp_client.py
│   ├── event_handler.py
│   └── ui/
│       ├── __init__.py
│       ├── login_view.py
│       └── main_view.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Cài đặt và chạy trên Windows

Yêu cầu Python 3.12. Mở Terminal hoặc PowerShell tại thư mục gốc của repository.

### 1. Tạo môi trường và cài thư viện

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường, có thể chạy trực tiếp bằng `.venv\Scripts\python.exe` hoặc dùng Command Prompt.

### 2. Khởi động Server

Mở Terminal thứ nhất tại thư mục gốc:

```powershell
python -m server.main
```

Server lắng nghe trên mọi giao diện mạng tại cổng TCP `9999`. Giữ cửa sổ này mở trong khi sử dụng ứng dụng.

### 3. Khởi động Client

Mở Terminal thứ hai tại cùng thư mục:

```powershell
python -m client.main
```

Mở thêm cửa sổ Client bằng cách chạy lại lệnh để thử nhiều người dùng. Khi thử trên cùng máy, giữ `SERVER_IP = "127.0.0.1"` trong `common/constants.py`.

## Chạy qua mạng LAN

1. Khởi động Server trên máy chủ và xác định địa chỉ IPv4 nội bộ của máy đó.
2. Trên các máy Client, sửa `SERVER_IP` trong `common/constants.py` thành IPv4 của máy chạy Server, ví dụ `192.168.1.10`.
3. Cho phép Python hoặc cổng TCP `9999` qua Windows Firewall trên máy Server nếu được yêu cầu.
4. Chạy Client bằng `python -m client.main`.

Không mở cổng này ra Internet công cộng; bản demo chưa có mã hóa TLS hay cơ chế xác thực tài khoản.

## Giao thức thông điệp

Các loại thông điệp: `LOGIN`, `LOGOUT`, `USER_LIST`, `CHAT_ALL`, `CHAT_PRIVATE`, `SYSTEM`. Mỗi thông điệp là một JSON object với các trường `type`, `sender`, `receiver`, `payload`, kết thúc bằng `\n`. Vì TCP là luồng byte, chương trình phải tách thông điệp theo dấu xuống dòng thay vì giả định mỗi lần `recv()` tương ứng đúng một thông điệp.

## Kiểm thử demo

1. Khởi động Server.
2. Mở hai hoặc ba Client với các tên khác nhau.
3. Gửi tin nhắn trong phòng chat chung và xác nhận các Client khác nhận được.
4. Chọn một người trong danh sách để chat riêng; xác nhận người không được chọn không nhận tin nhắn riêng.
5. Thử đăng nhập hai lần với cùng một tên và thử tên không hợp lệ.
6. Đóng một Client và kiểm tra danh sách người dùng được cập nhật.

## Giới hạn hiện tại

- Tin nhắn chỉ tồn tại trong phiên chạy; không lưu lịch sử vào cơ sở dữ liệu.
- Chưa có mã hóa TLS, tài khoản/mật khẩu hoặc gửi file.
- Server dành cho bài tập và demo trong mạng tin cậy.
