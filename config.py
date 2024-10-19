from enum import Enum

HOST = '127.0.0.1'
PORT = 8000
DATA_LENGTH = 10240


class ServerCommandType(Enum):
    CLOSE = 0
    CONNECT = 1
    GET_MINE = 2
    SET_NAME = 3
    ERR = 4
    INFO = 5