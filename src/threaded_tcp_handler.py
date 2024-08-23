import logging
import os
import socketserver

from src.filehandler import make_personal_dir, deserialize, unpack, get_filepaths, \
    pack, serialize
from src.server_config import ServerConfig
from src.streamutil import split_stream, end_reached, remove_delimiter


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, request_handler_class, user_queue, server_config):
        socketserver.ThreadingMixIn.__init__(self)
        socketserver.TCPServer.__init__(self, server_address, request_handler_class)
        self.user_queue = user_queue
        self.server_config = server_config


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server: ThreadedTCPServer):
        super().__init__(request, client_address, server)
        self.server: ThreadedTCPServer = server

    def handle(self):
        user_queue = self.server.user_queue
        server_config = self.server.server_config
        data, client_address = self.get_request(self, server_config)
        task_directory = self.process_request(data, client_address)
        result_directory = task_directory + '/result'
        os.mkdir(result_directory)

        user_queue.enqueue_task(task=task_directory)
        self.await_task_completion(result_directory + '/output')
        response = prepare_response(result_directory)
        self.send(self, response, server_config)

        if server_config.isTest:
            self.shutdown()

        self.request.close()



    def send(self, tcp_handler, response, server_config: ServerConfig):
        for i in range(0, len(response), server_config.chunk_size):
            chunk = response[i:i + server_config.chunk_size]
            tcp_handler.request.sendall(chunk)

    def shutdown(self):
        self.event.set()
        self.server.shutdown()
        logging.info("Server Shutdown")

    def get_request(self, tcp_handler, server_config: ServerConfig):
        data = b''
        client_address = ''
        download = ''
        only_bin_file = True

        while True:
            chunk = tcp_handler.request.recv(server_config.chunk_size)
            data += chunk

            if not client_address:
                client_address, stream = split_stream(data)
                download, stream = split_stream(stream)
                logging.info("Receiving data from '{}' {}.".format(client_address, tcp_handler.client_address))
                data = stream

            if len(chunk) < server_config.chunk_size or end_reached(chunk):
                break

        data = remove_delimiter(data)
        return data, client_address

    def await_task_completion(self, directory):
        while True:
            if not os.path.exists(directory):
                continue
            for filename in os.listdir(directory):
                if filename.endswith('.bin'):
                    return

    def process_request(self, data, user, ):  # Server
        task_dir = make_personal_dir(user, self.server.server_config.receive)
        filepath = '/'.join([task_dir, self.server.server_config.request])

        deserialize(data, filepath)
        unpack(filepath, task_dir)
        os.remove(filepath)

        return task_dir


def prepare_response(result_directory):
    files = get_filepaths(result_directory)
    filepath = '/'.join([result_directory, 'result.zip'])
    pack(files, filepath)


    return serialize(filepath)
