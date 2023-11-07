from simulationflow.filehandler import process_request
from simulationflow.taskhandler import user_queue
from simulationflow.macutil import split_stream

from docs.config import Config
import socketserver
import threading

config = Config().get()
chunk_size = config['chunk size']


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = b''
        client_address = ''

        while True:
            chunk = self.request.recv(chunk_size)
            
            if not client_address:
                client_address, stream = split_stream(chunk)
                data += stream
                continue

            if not chunk:
                break

            data += chunk
 
        print("Data received by {}".format(client_address))

        # self.request.sendall(bytes("Success", "utf-8"))
        task_directory = process_request(data, client_address)
        user_queue.enqueue_task(task=task_directory)


if __name__ == '__main__':
    HOST, PORT = config['host'], config['port']

    with socketserver.TCPServer((HOST, PORT), ThreadedTCPHandler) as server:
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        server_thread.join()
