from enum import Enum
from typing import List
import json

HOST = '127.0.0.1'
PORT = 8000
DATA_LENGTH = 10240


class MessageType(Enum):
    CLOSE = 0
    CONNECT = 1
    GET_MINE = 2
    SET_NAME = 3
    ERR = 4
    INFO = 5
    GET_OWNER = 6
    
    
def create_message(type: MessageType, *args: List[str | int | float]):
    arg_count: int = len(args)
    i: int = 0
    payload = {
        "type": type,
        "data": {},
    }
    if i % 2 != 0:
        raise ValueError("Command payload args must be key-value pairs.")

    while i < arg_count - 1:
        payload["data"][args[i]] = args[i + 1]
    return json.dumps(payload)