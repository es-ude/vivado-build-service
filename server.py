from src.filehandler import process_request, prepare_response
from src.streamutil import split_stream, end_reached, remove_delimiter
from src.taskhandler import user_queue
from docs.config import Config

import socketserver
import threading
import logging
import os

logging.getLogger().setLevel(logging.INFO)

config = Config().get()
chunk_size = config['chunk size']


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = b''
        client_address = ''
        
        while True:
            chunk = self.request.recv(chunk_size)
            data += chunk

            if len(chunk) < chunk_size or end_reached(chunk):
                break

            if not client_address:
                client_address, stream = split_stream(data)
                data = stream
 
        data = remove_delimiter(data)
        logging.info("Receiving data from '{}'.".format(client_address))

        task_directory = process_request(data, client_address)
        user_queue.enqueue_task(task=task_directory)

        result_directory = task_directory + '/result'
        infofile_path = result_directory + '/completed.txt'

        while True:
            if os.path.isfile(infofile_path):
                break
        
        response = prepare_response(result_directory)

        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            self.request.sendall(chunk)

        os.rmdir(task_directory)
        self.request.close()


if __name__ == '__main__':
    HOST, PORT = config['host'], config['port']

    with socketserver.TCPServer((HOST, PORT), ThreadedTCPHandler) as server:
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        server_thread.join()
