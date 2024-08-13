import dataclasses

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




@dataclasses.dataclass
class ServerConfig:
    chunk_size: int
    PORT: str
    tcl_script: str
    constraints: str
    bash_script: str
    test_bash_script: str
    vnc_user: str


class Server:
    def __init__(self):
        self.chunk_size: int = 0
        self.PORT: str = ''
        self.tcl_script: str = ''
        self.constraints: str = ''
        self.bash_script: str = ''
        self.test_bash_script: str = ''
        self.vnc_user: str = ''

    def load_config_from_server_config(self, server_config: ServerConfig):
        pass

    def load_config_from_toml(self) -> None:
        self.server_config = ServerConfig(
            chunk_size=config['Connection']['chunk_size']
        )

        PORT = config['Connection']['port']
        tcl_script = os.path.abspath(config['Paths']['tcl_script'])
        constraints = os.path.abspath(config['Paths']['constraints'])
        bash_script = [os.path.abspath(config['Paths']['bash_script'] + 'unix.sh')]
        test_bash_script = [os.path.abspath(config['Test']['bash_script'])]
        vnc_user = config['VNC']['username']


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


def get_request(tcp_handler):
    data = b''
    client_address = ''
    download = ''
    only_bin_file = True

    while True:
        chunk = tcp_handler.request.recv(chunk_size)
        data += chunk

        if not client_address:
            client_address, stream = split_stream(data)
            download, stream = split_stream(stream)
            logging.info("Receiving data from '{}' {}.".format(client_address, tcp_handler.client_address))
            data = stream

        if len(chunk) < chunk_size or end_reached(chunk):
            break    

    data = remove_delimiter(data)
    return data, client_address


def send(tcp_handler, response):
    for i in range(0, len(response), chunk_size):
        chunk = response[i:i + chunk_size]
        tcp_handler.request.sendall(chunk)


def await_task_completion(directory):
    while True:
        if not os.path.exists(directory):
            continue
        for fname in os.listdir(directory):
            if fname.endswith('.bin'):
                return


def task_worker(user_queue, event, testing=False):
    with ThreadPoolExecutor(max_workers=12) as executor:
        while True:
            if event.is_set():
                break

            task = user_queue.dequeue_task()
            if task is None:
                continue

            executor.submit(execute, task, config, event, testing)
    

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def setup_taskhandler(testing=False):
    user_queue = UserQueue()
    taskhandler_thread = threading.Thread(target=task_worker, args=(user_queue, event, testing))
    taskhandler_thread.daemon = True
    taskhandler_thread.start()
    return user_queue


server_is_running = False
def setup_server(user_queue, testing=False):
    global server_is_running

    with ThreadPoolExecutor(max_workers=12) as executor:
        with ThreadedTCPServer(('localhost', PORT), ThreadedTCPHandler) as server:
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


def shutdown(server):
    event.set()
    server.shutdown()
    logging.info("Server Shutdown")


def setup(testing=False):
    user_queue = setup_taskhandler(testing)
    setup_server(user_queue, testing)


def main():
    try:
        setup()
    except Exception as e:
        logging.error("Something went wrong: {}".format(e))


if __name__ == '__main__':
    main()
