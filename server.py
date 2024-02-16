from src.filehandler import process_request, prepare_response
from src.streamutil import split_stream, end_reached, remove_delimiter
from src.taskhandler import UserQueue, execute
from docs.config import Config

import socketserver
import threading
import logging
import os

logging.getLogger().setLevel(logging.INFO)

config = Config().get()
chunk_size = config['chunk size']
HOST, PORT = config['host'], config['port']

class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        user_queue = self.server.user_queue
        
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
        logging.info("Receiving data from '{}' {}.".format(client_address, self.client_address))

        task_directory = process_request(data, client_address)
        result_directory = task_directory + '/result'
        os.mkdir(result_directory)

        user_queue.enqueue_task(task=task_directory)

        await_task_completion(result_directory + '/output')

        response = prepare_response(result_directory)

        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            self.request.sendall(chunk)

        self.request.close()


def await_task_completion(directory):
    while True:
        if not os.path.exists(directory):
            continue
        for fname in os.listdir(directory):
            if fname.endswith('.bin'):
                return


def Task_worker(user_queue):
    while True:
        task = user_queue.dequeue_task()

        if task is None:
            continue

        execute(task)


if __name__ == '__main__':
    user_queue = UserQueue()
    taskhandler_thread = threading.Thread(target=Task_worker, args=(user_queue, ))
    taskhandler_thread.daemon = True
    taskhandler_thread.start()    

    with socketserver.TCPServer((HOST, PORT), ThreadedTCPHandler) as server:
        server.user_queue = user_queue
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        server_thread.join()
