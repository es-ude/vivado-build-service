from unittest import TestCase
import filecmp
import logging
import time
import os

from src import config
from src.filehandler import reset
import server
import client
import threading

logging.getLogger().setLevel(logging.INFO)

class Test(TestCase):
    def setUp(self) -> None:
        try:
            reset()
            HOST, PORT = config['host'], config['port']

            def run_server():
                server.setup(testing=True)

            def run_client():
                client.setup(HOST, PORT, testing=True)

            server_thread = threading.Thread(target=run_server)
            client_thread = threading.Thread(target=run_client)

            server_thread.start()
            client_thread.start()

            server_thread.join()
            client_thread.join()
        
        except Exception as e:
            print(f"Error: {e}")


    def tearDown(self) -> None:
        reset()
        return super().tearDown()

    def test_files_equal(self):
        test_packet = os.listdir(config['test packet'])
        directory_server = 'tmp/server/testing/1/tests/test_packet'
        directory_test_packet = 'tests/test_packet'

        try:
            index = 0
            for file in os.listdir(directory_server):
                abspath = os.path.abspath(os.path.join(directory_server, file))
                test_packet_abspath = os.path.abspath(os.path.join(directory_test_packet, test_packet[index]))

                self.assertTrue(filecmp.cmp(abspath, test_packet_abspath, shallow=False))
                logging.info(f"File {index + 1}: Success")
                index += 1
        except Exception as e:
            self.fail(f"File {index + 1}: Failure\nError: {e}")