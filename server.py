from person import Person
from config import *
import socket
from threading import Thread
import json
from typing import List, Dict, Self
import csv
from random import shuffle, randint


class ServerClient:
    def __init__(self, id: int, address, socket: socket.socket) -> None:
        self.id = id
        self.address = address
        self.socket = socket
        self.name = f"anon#{self.id}"


class Server:
    servers: Dict[int, Self] = {}

    @staticmethod
    def get(port: int = PORT):
        if port not in Server.servers:
            Server(PORT)

        return Server.servers[port]

    @staticmethod
    def loadDataTable(filename: str) -> List[Dict[str, str | int | float]]:
        with open(filename, mode="r") as file:
            source = csv.reader(file)
            header = next(source)

            table = []
            for row in source:
                dict_row = {}
                for index, column in enumerate(header):
                    dict_row[column.lower()] = row[index]
                table.append(dict_row)
            return table

    def __init__(self, port: int, source_filename: str, min_data_length: int = 10, max_data_length: int = 100) -> None:
        if port in Server.servers and Server.servers[port].running:
            raise Exception(f"There is another server running on {HOST}:{port}")
        self.host = HOST
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[int, ServerClient] = {}
        self.running = False
        self.last_client_id = 0
        self.source_filename = source_filename
        self.data: List[Person] = []
        self.min_data_length: int = min_data_length
        self.max_data_length: int = max_data_length
        Server.servers[self.port] = self
        self.load_data()

    def load_data(self):
        try:
            data_table = Server.loadDataTable(self.source_filename)
            self.data = list(
                map(
                    lambda row: Person(
                        row["'id'"], row["'firstname'"], row["'lastname'"], row["'email'"], row["'city'"]
                    ),
                    data_table,
                )
            )
            print(f"successfully loaded {len(self.data)} person's data ...")
        except Exception as ex:
            print(ex)
            print(
                "Server could not load data:",
                ex,
                "\n\nServer continues running, but has no data to distribute to clients",
            )
            self.data.clear()

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen()

        print(f"Server started listening on {self.host}:{self.port}")

        self.running = True
        while self.running:
            client_socket, client_addr = self.socket.accept()
            self.last_client_id += 1

            Thread(
                target=self.handle_client, args=(ServerClient(self.last_client_id, client_addr, client_socket),)
            ).start()
        self.is_running = False

    def handle_client(self, client: ServerClient):
        print(f"{client.address} is trying to connect ...")
        self.clients[client.id] = client

        allocated_count = self.try_to_allocate_data(client)
        print(f"allocated {allocated_count} person's data to client#{client.id} with the ip:{client.address}")

        client.socket.send(
            bytes(
                create_message(
                    MessageType.CONNECT.value, "id", client.id, "name", client.name, "allocated", allocated_count
                ),
                "utf-8",
            )
        )

        while True:
            data = client.socket.recv(DATA_LENGTH)

            if not data:
                try:
                    client.socket.send(
                        bytes(create_message(MessageType.CLOSE.value), "utf-8")
                    )  # inform client that the connection is closed.
                except:
                    pass
                break

            payload = json.loads(data)

            match payload["type"]:
                case MessageType.CLOSE.value:
                    break
                case MessageType.GET_MINE.value:
                    your_data = [person.to_dict() for person in self.data_owned_by(client.id)]
                    client.socket.send(bytes(create_message(MessageType.GET_MINE.value, "data", your_data), "utf-8"))
                case MessageType.GET_OWNER.value:
                    try:
                        if not "targets" in payload["data"]:
                            raise ValueError("You must specify the id of the data you're seeking.")
                        result = self.get_data_owners(payload["data"]["targets"])
                        client.socket.send(bytes(create_message(MessageType.GET_OWNER.value, "data", result), "utf-8"))
                        print(f"sent some data and their owners to client#{client.id}")
                    except Exception as ex:
                        print(f"failed to sent data & their owner to client#{client.id} because:", ex)
                        client.socket.send(bytes(create_message(MessageType.ERR.value, "msg", ex.__str__()), "utf-8"))
                case MessageType.SET_NAME.value:
                    try:
                        if "data" in payload and "name" in payload["data"] and payload["data"]["name"] != client.name:
                            client.name = str(payload["data"]["name"])
                            print(f"client#{client.id} has been renamed to {client.name}")
                            client.socket.send(
                                bytes(
                                    create_message(
                                        MessageType.INFO.value,
                                        "msg",
                                        f"You successfully renamed your client to {client.name}.",
                                    )
                                )
                            )
                        else:
                            raise ValueError("To rename you must provide a new name.")
                    except Exception as ex:
                        client.socket.send(bytes(create_message(MessageType.ERR.value, "msg", ex.__str__()), "utf-8"))
                        print(f"client#{client.id} failed to rename because:", ex)
                case _:
                    client.socket.send(
                        bytes(
                            create_message(MessageType.ERR.value, "msg", "You have sent an unknown request!"), "utf-8"
                        )
                    )
                    print(f"client#{client.id} has sent an unknown request! request data:", data)
        self.disconnect_client(client)

    def get_data_owners(self, data_ids: List[int] | int):
        result = []
        if not isinstance(data_ids, list):
            data_ids = [data_ids]

        for id in data_ids:
            id = int(id)
            person = next((person for person in self.data if person.id == id), None)
            if person:
                data = person.to_dict()
                data["owner"] = self.clients[person.owner_id].name if not person.is_free else None
                result.append(data)
        return result

    def disconnect_client(self, client: ServerClient):
        try:
            client.socket.close()
        except:
            pass
        print(f"client#{client.id} disconnected.")
        del self.clients[client.id]

        released_data = self.data_owned_by(client_id=client.id)
        if not released_data:
            print(f"client{client.id} has no data, so there is no data to be redistributed.")
            return
        clients_in_need = self.get_clients_by_poverty()

        i, end = 0, len(released_data)
        for client in clients_in_need:
            allocation_length = i + self.data_allocation_length(end - i)

            while i < allocation_length:
                released_data[i].reallocate(client.id)
        print(f"client#{client.id}'s allocated data has been redistributed among other clients.")

    def data_owned_by(self, client_id) -> List[Person]:
        return [person for person in self.data if person.is_owned_by(client_id)]

    def get_clients_by_poverty(self):
        return sorted(self.clients.values(), key=lambda client: len(self.data_owned_by(client.id)))

    def data_allocation_length(self, available_data_length: int):
        return (
            randint(self.min_data_length, min(available_data_length, self.max_data_length))
            if available_data_length >= self.min_data_length
            else available_data_length
        )

    def try_to_allocate_data(self, client: ServerClient):
        free_data: List[Person] = [person for person in self.data if person.is_free]
        if not free_data:
            return 0
        shuffle(free_data)

        allocated_count = 0
        for i in range(self.data_allocation_length(len(free_data))):
            try:
                free_data[i].allocate(client.id)
                allocated_count += 1
            except:
                pass

        return allocated_count


if __name__ == "__main__":
    Server(PORT, "./RandomData.csv").listen()
