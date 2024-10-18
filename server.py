from person import Person
from config import *
import socket
from threading import Thread
import json
from typing import List, Dict
import csv

class ServerClient:
    def __init__(self, id: int, address: socket._RetAddress, socket: socket.socket) -> None:
        self.id = id
        self.address = address
        self.socket = socket


class Server:
    servers = {}

    @staticmethod
    def get(port: int = PORT):
        if port not in Server.servers:
            Server.servers[port] = Server(PORT)

        return Server.servers[port]


    @staticmethod
    def createCommand(type: ServerCommandType, *args: List[str | int | float]):
        arg_count: int = len(args)
        i: int = 0
        payload = {'type': type, }
        if i % 2 != 0:
            raise ValueError('Command payload args must be key-value pairs.')

        while i < arg_count - 1:
            payload[args[i]] = args[i + 1]
        return json.dumps(payload)

    @staticmethod
    def loadDataTable(filename: str) -> List[Dict[str, str|int|float]]:
        with open(filename, mode='r') as file:
            source = csv.reader(file)
            header = next(source)

            table = []
            for row in source:
                dict_row = {}
                for index, column in enumerate(header):
                    dict_row[column.lower()] = row[index]
                table.append(dict_row)
            return table

    def __init__(self, port: int, source_filename:str) -> None:
        if port in Server.servers:
            raise Exception(f'There is another server running on {HOST}:{port}')
        self.host = HOST
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[int, ServerClient] = {}
        self.running = False
        self.last_client_id = 0
        self.source_filename = source_filename
        self.data: List[Person] = []
    
    def load_data(self):
        try:
            data_table = Server.loadDataTable(self.source_filename)
            self.data = list(map(lambda row: Person(int(row['id']), row['firstname'], row['lastname'], row['email'], row['city']), data_table))
        except Exception as ex:
            print('Server could not load data:', ex, '\n\nServer continues running, but has no data to distribute to clients')
            self.data.clear();

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen()

        print(f'Server started listening on {self.host}:{self.port}')

        self.running = True
        while self.running:
            client_socket, client_addr = self.socket.accept()
            self.last_client_id += 1

            Thread(target=self.handle_client, args=(ServerClient(self.last_client_id, client_addr, client_socket))).start()


    def handle_client(self, client: ServerClient):
        print(f'{client.address} is trying to connect ...')
        self.clients[client.id] = client
        client.socket.sendall(Server.createCommand(ServerCommandType.CONNECT, 'id', client.id))

        self.try_to_allocate_data(client)
        while True:
            data = client.socket.recv(DATA_LENGTH)

            if not data:
                break

            payload = json.loads(data)

            match payload['type']:
                case _:
                    # TODO: handle commands
                    pass

        client.socket.close()
        del self.clients[client.id]

    def try_to_allocate_data(self, client: ServerClient):
        pass