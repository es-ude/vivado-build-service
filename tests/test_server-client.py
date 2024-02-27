from unittest import TestCase, mock
from io import BytesIO
import socket
import threading
import time

from docs.config import Config
import server
import client

config = Config().get()
HOST, PORT = config['test host'], config['test port']

class TestServerClientCommunication(TestCase):
    def setUp(self):
        self.server_thread = threading.Thread(target=server.main, args=(HOST, PORT))
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(1)

    def tearDown(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server.HOST, server.PORT))
            s.sendall(b'STOP_SERVER')
        self.server_thread.join()

    def test_server_client_communication(self):
        with mock.patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value = mock_socket
            mock_socket.recv.side_effect = [b'example_response']

            client.create_socket()

            mock_socket.send.assert_called_once_with(b'example_data')

    def test_server_response(self):
        with mock.patch('socketserver.BaseRequestHandler.request') as mock_socket:
            fake_request = b'example_request'
            mock_socket.recv.return_value = fake_request

            handler = server.ThreadedTCPHandler(mock.Mock(), mock.Mock())
            handler.handle()

            mock_socket.sendall.assert_called_once()

