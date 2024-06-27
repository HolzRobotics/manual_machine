import json
import socket
from typing import Callable
from logger import logger


DEFAULT_BUFFER_SIZE = 1024
DEFAULT_SOCKET_CONNECTIONS = 5


def start_server_socket(host: str, port: int, callback: Callable):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(DEFAULT_SOCKET_CONNECTIONS)

    while True:
        client_socket, _ = server_socket.accept()
        data_bytes = client_socket.recv(DEFAULT_BUFFER_SIZE)
        try:
            json_data = json.loads(data_bytes.decode())
            callback(json_data)
        except Exception as e:
            logger.error(f'Не удалось обработать сообщение: {e}')
