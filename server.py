from src.filehandler import process_request, prepare_response
from src.streamutil import split_stream, end_reached, remove_delimiter
from src.taskhandler import UserQueue, execute
from src import config

from concurrent.futures import ThreadPoolExecutor
import socketserver
import threading
import logging
import os

logging.getLogger().setLevel(logging.INFO)
event = threading.Event()

server_is_running = False
chunk_size = config['Connection']['chunk_size']
HOST, PORT = config['Connection']['host'], config['Connection']['port']


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        user_queue = self.server.user_queue
        testing = self.server.testing
        data, client_address = get_request(self)
        task_directory = process_request(data, client_address)
        result_directory = task_directory + '/result'
        os.mkdir(result_directory)

        user_queue.enqueue_task(task=task_directory)
        await_task_completion(result_directory + '/output')
        response = prepare_response(result_directory)
        send(self, response)

        if testing:
            shutdown(self.server)

        self.request.close()


def get_request(tcpHandler):
    data = b''
    client_address = ''
    
    while True:
        chunk = tcpHandler.request.recv(chunk_size)
        data += chunk

        if not client_address:
            client_address, stream = split_stream(data)
            logging.info("Receiving data from '{}' {}.".format(client_address, tcpHandler.client_address))
            data = stream

        if len(chunk) < chunk_size or end_reached(chunk):
            break    

    data = remove_delimiter(data)
    return data, client_address


def send(tcpHandler, response):
    for i in range(0, len(response), chunk_size):
        chunk = response[i:i + chunk_size]
        tcpHandler.request.sendall(chunk)


def await_task_completion(directory):
    while True:
        if not os.path.exists(directory):
            continue
        for fname in os.listdir(directory):
            if fname.endswith('.bin'):
                return


def Task_worker(user_queue, event, testing=False):
    with ThreadPoolExecutor(max_workers=12) as executor:
        while True:
            if event.is_set():
                break

            task = user_queue.dequeue_task()
            if task is None:
                continue

            executor.submit(execute, task, event, testing)
    

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def setup_taskhandler(testing=False):
    user_queue = UserQueue()
    taskhandler_thread = threading.Thread(target=Task_worker, args=(user_queue, event, testing))
    taskhandler_thread.daemon = True
    taskhandler_thread.start()
    return user_queue


def setup_server(user_queue, testing=False):
    global server_is_running

    with ThreadPoolExecutor(max_workers=12) as executor:
        with ThreadedTCPServer((HOST, PORT), ThreadedTCPHandler) as server:
            server.user_queue = user_queue
            server.testing = testing
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            server_thread.join()

            if not server_is_running:
                server_is_running = True
                logging.info("Server is running.")
                logging.info("Waiting for connection...")


def setup(testing=False):
    user_queue = setup_taskhandler(testing)
    setup_server(user_queue, testing)


def shutdown(server):
    event.set()
    server.shutdown()
    logging.info("Server Shutdown")


def main():
    logging.info("Server starting up...")
    setup()


if __name__ == '__main__':
    main()