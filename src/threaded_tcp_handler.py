import os
import logging
import socketserver

from src.user_queue import Task
from src.config import ServerConfig, GeneralConfig
from src.streamutil import split_stream, end_reached, remove_delimiter
from src.filehandler import make_personal_dir_and_get_task, deserialize, unpack, get_filepaths, pack, serialize


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, request_handler_class, user_queue, server_config, event, general_config):
        socketserver.ThreadingMixIn.__init__(self)
        socketserver.TCPServer.__init__(self, server_address, request_handler_class)
        self.event = event
        self.user_queue = user_queue
        self.server_config = server_config
        self.general_config = general_config


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server: ThreadedTCPServer):
        super().__init__(request, client_address, server)
        self.server: ThreadedTCPServer = server

    def handle(self):
        user_queue = self.server.user_queue
        server_config = self.server.server_config
        general_config = self.server.general_config
        data, client_address, only_bin = self.get_request(self, server_config)
        task = self.process_request(data, client_address, only_bin)
        task_directory = task.path()
        result_directory = task_directory + '/result'
        os.mkdir(result_directory)

        # use task class:
        user_queue.enqueue_task(task)

        await_task_completion(directory=result_directory + '/output')
        response = prepare_response(result_directory, task_directory)
        self.send(self, response, server_config)
        self.request.close()

    def send(self, tcp_handler, response, general_config: GeneralConfig):
        for i in range(0, len(response), self.server.general_config.chunk_size):
            chunk = response[i:i + self.server.general_config.chunk_size]
            tcp_handler.request.sendall(chunk)

    def shutdown(self):
        self.server.shutdown()
        logging.info(":TCP: Server Shutdown")

    def get_request(self, tcp_handler, general_config: GeneralConfig):
        data = b''
        client_address = ''
        only_bin_file = True

        while True:
            chunk = tcp_handler.request.recv(self.server.general_config.chunk_size)
            data += chunk

            if not client_address:
                client_address, stream = split_stream(data, self.server.general_config.delimiter.encode())
                only_bin_file, stream = split_stream(stream, self.server.general_config.delimiter.encode())
                only_bin_file = bool(only_bin_file)
                logging.info(":TCP: Receiving data from '{}' {}.\n".format(client_address, tcp_handler.client_address))
                data = stream

            if (len(chunk) < self.server.general_config.chunk_size or
                    end_reached(chunk, self.server.general_config.delimiter)):
                break

        data = remove_delimiter(data, self.server.general_config.delimiter)
        return data, client_address, only_bin_file

    def process_request(self, data, user, only_bin) -> Task:  # Server
        task = make_personal_dir_and_get_task(user, self.server.server_config.receive_folder, only_bin)
        task_dir = task.path()
        filepath = '/'.join([task_dir, self.server.general_config.request_file])

        deserialize(data, filepath)
        unpack(filepath, task_dir)
        os.remove(filepath)

        return task


def await_task_completion(directory):
    while True:
        if not os.path.exists(directory):
            continue
        for filename in os.listdir(directory):
            if filename.endswith('.bin'):
                return


def prepare_response(result_directory, task_directory):
    files = get_filepaths(result_directory)
    filepath = '/'.join([result_directory, 'result.zip'])
    pack(base_folder=task_directory, origin=files, destination=filepath)

    return serialize(filepath)
