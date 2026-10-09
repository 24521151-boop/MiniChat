import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Cấu hình logging cơ bản
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# 1. Danh sách loại thông điệp hợp lệ
class MsgType(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    USER_LIST = "USER_LIST"
    CHAT_ALL = "CHAT_ALL"
    CHAT_PRIVATE = "CHAT_PRIVATE"
    SYSTEM = "SYSTEM"

    # Các loại thông điệp phục vụ gửi file qua TCP.
    # FILE_OFFER: thông tin file (payload là JSON dạng chuỗi, ví dụ tên file/kích thước).
    # FILE_ACCEPT / FILE_REJECT: người nhận chấp nhận hoặc từ chối file.
    # FILE_CHUNK: một phần dữ liệu file (payload chứa dữ liệu đã mã hóa Base64).
    # FILE_END: báo đã gửi xong file.
    # FILE_CANCEL: hủy phiên gửi file.
    FILE_OFFER = "FILE_OFFER"
    FILE_ACCEPT = "FILE_ACCEPT"
    FILE_REJECT = "FILE_REJECT"
    FILE_CHUNK = "FILE_CHUNK"
    FILE_END = "FILE_END"
    FILE_CANCEL = "FILE_CANCEL"


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
    # Tự động chuyển đổi string sang Enum nếu cần.
    if isinstance(msg_type, str):
        try:
            msg_type = MsgType(msg_type)
        except ValueError as exc:
            raise ValueError(f"Loại thông điệp không hợp lệ: {msg_type!r}") from exc

    if not all(isinstance(value, str) for value in (sender, receiver, payload)):
        raise TypeError("sender, receiver và payload phải là chuỗi")

    data = {
        "type": msg_type.value,
        "sender": sender,
        "receiver": receiver,
        "payload": payload,
    }

    # Ký tự xuống dòng đánh dấu kết thúc một thông điệp trong TCP stream.
    return json.dumps(data, ensure_ascii=False) + "\n"


# 4. Phân tích và kiểm tra thông điệp JSON
def parse_message(message_str: str) -> Optional[Message]:
    try:
        data = json.loads(message_str)

        if not isinstance(data, dict):
            logger.warning("Dữ liệu nhận được không phải dạng dict")
            return None

        required_fields = ("type", "sender", "receiver", "payload")
        if not all(field in data for field in required_fields):
            logger.warning(
                "Thiếu trường dữ liệu bắt buộc. Có: %s",
                list(data.keys()),
            )
            return None

        if not all(isinstance(data[field], str) for field in required_fields):
            logger.warning("Kiểu dữ liệu các trường không phải là chuỗi")
            return None

        msg_type = MsgType(data["type"])

        return Message(
            msg_type=msg_type,
            sender=data["sender"],
            receiver=data["receiver"],
            payload=data["payload"],
        )

    except json.JSONDecodeError:
        logger.warning("Thông điệp không phải JSON hợp lệ: %s...", message_str[:50])
        return None
    except ValueError:
        logger.warning(
            "Loại thông điệp không hợp lệ: %s",
            data.get("type") if "data" in locals() and isinstance(data, dict) else "Unknown",
        )
        return None
    except TypeError:
        logger.warning("Kiểu dữ liệu thông điệp không hợp lệ")
        return None
