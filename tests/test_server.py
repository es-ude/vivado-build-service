from unittest import TestCase
import filecmp
import time
import os

from docs.config import Config
from src.filehandler import reset
import server
import client

config = Config().get()

import threading

class Test(TestCase):
    def setUp(self) -> None:
        try:
            reset()
            HOST, PORT = config['host'], config['port']

            # Define functions to run in threads
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

            return super().setUp()
        
        except Exception as e:
            print(f"Error: {e}")


    def tearDown(self) -> None:
        reset()
        return super().tearDown()

    def test_file_transfer(self):
        test_packet = os.listdir(config['test packet'])
        directory_server = 'tmp/server/testing/1/tests/test_packet'
        directory_test_packet = 'tests/test_packet'

        try:
            index = 0
            for file in os.listdir(directory_server):
                abspath = os.path.abspath(os.path.join(directory_server, file))
                test_packet_abspath = os.path.abspath(os.path.join(directory_test_packet, test_packet[index]))
                print("\n\nFILECOMPARE: " + abspath + "\n" + test_packet_abspath + "\n")
                self.assertTrue(filecmp.cmp(abspath, test_packet_abspath, shallow=False))
                index += 1
        except:
            self.fail()