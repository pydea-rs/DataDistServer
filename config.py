from enum import Enum

HOST = '127.0.0.1'
PORT = 8000
DATA_LENGTH = 1024


class ServerCommandType(Enum):
    CONNECT = 1

