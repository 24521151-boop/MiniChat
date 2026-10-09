

# ==========================================
# CẤU HÌNH MẠNG
# ==========================================
# Địa chỉ IP của Server (127.0.0.1 dùng để chạy test trên cùng 1 máy)
# Khi chạy thực tế trên LAN, các máy Client cần trỏ về IP của máy chạy Server.
SERVER_IP = "127.0.0.1" 

TCP_PORT = 9999  # Cổng cho giao thức TCP (Đăng nhập, Chat)
UDP_PORT = 9998  # Cổng cho giao thức UDP (Heartbeat - Trạng thái)

BUFFER_SIZE = 4096  # Kích thước tối đa của một gói tin nhận được (bytes)
ENCODING = "utf-8"  # Chuẩn mã hóa ký tự

# ==========================================
# CẤU HÌNH TRẠNG THÁI (HEARTBEAT)
# ==========================================
# Thời gian (giây) Client gửi tín hiệu "Tôi vẫn đang sống" lên Server
HEARTBEAT_INTERVAL = 5 

# Thời gian (giây) Server chờ đợi. Nếu quá thời gian này không nhận được Heartbeat,
# Server sẽ đánh dấu Client đó là Offline.
TIMEOUT_THRESHOLD = 10 
