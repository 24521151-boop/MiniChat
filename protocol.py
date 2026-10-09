import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. Danh sách loại thông điệp hợp lệ
class MsgType(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    USER_LIST = "USER_LIST"
    CHAT_ALL = "CHAT_ALL"
    CHAT_PRIVATE = "CHAT_PRIVATE"
    SYSTEM = "SYSTEM"

# 2. Cấu trúc thống nhất của một thông điệp
@dataclass(frozen=True)
class Message:
    msg_type: MsgType
    sender: str = ""
    receiver: str = ""
    payload: str = ""

# 3. Đóng gói thông điệp thành JSON
def create_message(
    msg_type: MsgType | str,
    sender: str = "",
    receiver: str = "",
    payload: str = "",
) -> str:
    try:
        # Tự động chuyển đổi string sang Enum nếu cần
        if isinstance(msg_type, str):
            msg_type = MsgType(msg_type)
    except ValueError:
        raise ValueError(f"Loại thông điệp không hợp lệ: {msg_type!r}")

    if not all(isinstance(value, str) for value in (sender, receiver, payload)):
        raise TypeError("sender, receiver và payload phải là chuỗi")

    data = {
        "type": msg_type.value,
        "sender": sender,
        "receiver": receiver,
        "payload": payload,
    }

    # Thêm ký tự xuống dòng để đánh dấu kết thúc gói tin (xử lý TCP stream)
    return json.dumps(data, ensure_ascii=False) + "\n"

# 4. Phân tích và kiểm tra thông điệp JSON
def parse_message(message_str: str) -> Optional[Message]:
    try:
        data = json.loads(message_str)

        # 1. Kiểm tra kiểu dữ liệu gốc phải là dict
        if not isinstance(data, dict):
            logger.warning("Dữ liệu nhận được không phải dạng dict")
            return None

        # 2. Kiểm tra các trường bắt buộc
        required_fields = ("type", "sender", "receiver", "payload")
        if not all(field in data for field in required_fields):
            logger.warning(f"Thiếu trường dữ liệu bắt buộc. Có: {list(data.keys())}")
            return None

        # 3. Kiểm tra kiểu dữ liệu của các trường phải là chuỗi
        if not all(isinstance(data[field], str) for field in required_fields):
            logger.warning("Kiểu dữ liệu các trường không phải là chuỗi")
            return None

        # 4. Chuyển đổi type sang Enum (có thể ném ValueError)
        msg_type = MsgType(data["type"])

        # 5. Trả về đối tượng Message hoàn chỉnh
        return Message(
            msg_type=msg_type,
            sender=data["sender"],
            receiver=data["receiver"],
            payload=data["payload"],
        )

    except json.JSONDecodeError:
        logger.warning(f"Thông điệp không phải JSON hợp lệ: {message_str[:50]}...")
        return None
    except ValueError:
        logger.warning(f"Loại thông điệp không hợp lệ: {data.get('type') if 'data' in locals() else 'Unknown'}")
        return None
    except TypeError:
        logger.warning("Kiểu dữ liệu thông điệp không hợp lệ")
        return None
