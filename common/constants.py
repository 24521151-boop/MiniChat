# ==========================================
# CẤU HÌNH MẠNG
# ==========================================
# Địa chỉ IP của Server.
# 127.0.0.1 chỉ dùng khi Client và Server chạy trên cùng một máy.
# Khi chạy qua LAN, đổi thành địa chỉ IP của máy chạy Server.
SERVER_IP = "127.0.0.1"

# Cổng TCP dùng cho đăng nhập, chat và trao đổi dữ liệu gửi file.
TCP_PORT = 9999

# Kích thước bộ đệm nhận dữ liệu (bytes).
# Dữ liệu TCP cần được đọc theo từng dòng/thông điệp; không mặc định
# rằng một lần recv() tương ứng với một thông điệp hoàn chỉnh.
BUFFER_SIZE = 4096

# Chuẩn mã hóa cho dữ liệu văn bản.
ENCODING = "utf-8"
