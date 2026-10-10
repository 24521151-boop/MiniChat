import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class MsgType(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    USER_LIST = "USER_LIST"
    CHAT_ALL = "CHAT_ALL"
    CHAT_PRIVATE = "CHAT_PRIVATE"
    SYSTEM = "SYSTEM"

@dataclass(frozen=True)
class Message:
    msg_type: MsgType
    sender: str = ""
    receiver: str = ""
    payload: str = ""

def create_message(
    msg_type: MsgType | str,
    sender: str = "",
    receiver: str = "",
    payload: str = "",
) -> str:
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

    return json.dumps(data, ensure_ascii=False) + "\n"

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
