import socket
from config import *
import json
from typing import Dict, List


class Client:

    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id: int | None = None
        self.name: str | None = None
        self.connected = False

    def get_cmd(self):
        return input(
            "\nSelect your command:\n\t1 Get My Data\n\t2 Get Data Owners\n\t3 Change My Name\n\t0 Disconnect & Exit"
        )

    def show_data_table(self, data: List[Dict[str, int|str|float]], is_mine: bool = True):
        print(f'{'    ID':10}|{'     Firstname':20}|{'     Lastname':20}|{'     Email':30}|{'     City':20}|     Owner')
        print('       - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ')
        for person in data['data']:
            try:
                owner = '   You' if is_mine else (person['owner'] or '      -')
                print(f" {person['id']:9}| {person['firstname']:19}| {person['lastname']:19}| {person['email']:29}| {person['city']:19}| {owner}")
            except Exception as x:
                print('\t\tError in this row ...', x)
        print()

    def handle_menu(self):
        cmd: str = None
        while not cmd:
            cmd = self.get_cmd()
            match cmd:
                case '1':
                    self.socket.send(bytes(create_message(MessageType.GET_MINE.value), 'utf-8'))
                case '2':
                    id_list = None
                    while not id_list or not id_list.replace(' ', '').isnumeric():
                        if id_list: # Means this is not the first round of the loop & user has entered something which was not in the desired format,. so show error.
                            print('ERROR: Please enter the data in the format expected!')
                        id_list = input('Enter the desired data ID list, separated by space:')
                    self.socket.send(bytes(create_message(MessageType.GET_OWNER.value, 'targets', id_list.split()), 'utf-8'))
                case '3':
                    new_name = input('Now enter your new desired name:')
                    self.rename(new_name)
                case '0':
                    self.socket.send(bytes(create_message(MessageType.CLOSE.value), 'utf-8'))
                case _:
                    print('ERROR: Invalid command!')
                    cmd = None
        print('Please wait for server to answer ...')

    def connect(self):
        self.socket.connect((self.host, self.port))
        self.connected = True
        print("Please wait a little to connect ...")
        while self.connected:
            payload = self.socket.recv(DATA_LENGTH)

            if payload:
                payload = json.loads(payload)
            else:
                break
            if not payload or "type" not in payload or ("data" not in payload and payload['type'] != MessageType.CLOSE.value):
                print("Received some invalid format data from server which will be ignored ...")
                continue

            match payload["type"]:
                case MessageType.CONNECT.value:
                    data = payload["data"]
                    self.id = data["id"]
                    self.name = data["name"]
                    allocated_data_count = data["allocated"]
                    print(
                        f"You successfully are connected to server, known as {self.name} & your id in server is {self.id}."
                    )
                    if allocated_data_count and allocated_data_count > 0:
                        print(
                            f"\tAlso you've been allocated with some data, which actually is data related to {allocated_data_count} persons."
                        )
                    self.connected = True
                case MessageType.CLOSE.value:
                    self.connected = False
                case MessageType.ERR.value:
                    print('ERROR! ', payload['msg'])
                case MessageType.INFO.value:
                    print("> ", payload['msg'])
                case MessageType.GET_MINE.value:
                    self.show_data_table(payload['data'], True)
                case MessageType.GET_OWNER.value:
                    self.show_data_table(payload['data'], False)
            if self.connected:
                self.handle_menu()
            else:
                wanna_reconnect = input(
                    "You've been disconnected from the server. For reconnecting enter [Y/y], or enter anything else to close the app ..."
                )
                if wanna_reconnect and wanna_reconnect.lower() == 'y':
                    if not self.socket:
                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect((self.host, self.port))
                    self.connected = True

        print('Goodbye!')
        

if __name__ == '__main__':
    Client(HOST, PORT).connect()