from unittest import TestCase
import filecmp
import logging
import threading

import os
os.chdir('../../vivado-test-runner')

from src.filehandler import reset
from src import config
import server
import client

logging.getLogger().setLevel(logging.INFO)

test_packet = 'tests/build_dir'
HOST, PORT = config['Connection']['host'], config['Connection']['port']


class Test(TestCase):
    def setUp(self) -> None:
        def run_server():
            server.setup(testing=True)

        def run_client():
            client.build(HOST, PORT, testing=True)

        server_thread = threading.Thread(target=run_server)
        client_thread = threading.Thread(target=run_client)

        server_thread.start()
        client_thread.start()

        server_thread.join()
        client_thread.join()

    def test_files_equal(self):
        directory_server = 'tmp/server/test/1/'
        self.assertTrue(compare_directories(test_packet, directory_server))


def compare_directories(dir1, dir2):
    dirs_cmp = filecmp.dircmp(dir1, dir2, ignore=['result'])
    if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or \
            len(dirs_cmp.funny_files) > 0:
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not compare_directories(new_dir1, new_dir2):
            return False
    return True


def reset_test():
    test_dir_client = os.path.join(send_dir, 'test')
    test_dir_server = os.path.join(receive_dir, 'test')

    if os.path.isdir(test_dir_client) and os.path.isdir(test_dir_server):
        clear(test_dir_client)
        clear(test_dir_server)

        os.rmdir(test_dir_client)
        os.rmdir(test_dir_server)