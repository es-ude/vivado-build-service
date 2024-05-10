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
       # reset()
        return super().tearDown()

    def test_files_equal(self):
        directory_server = 'tmp/server/testing/1/'
        directory_test_packet = config['test packet']

        try:
            self.assertTrue(compare_directories(directory_test_packet, directory_server))

        except Exception as e:
            self.fail(e)


def compare_directories(dir1, dir2):
    dirs_cmp = filecmp.dircmp(dir1, dir2, ignore=['result'])
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or \
        len(dirs_cmp.funny_files)>0:
        return False
    (_, mismatch, errors) =  filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch)>0 or len(errors)>0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not compare_directories(new_dir1, new_dir2):
            return False
    return True
