import os
import time
import logging
import filecmp
import threading
from unittest import TestCase

from vbservice.buildserver import BuildServer
from vbservice.client import Client
from vbservice.src.config import ClientConfig, ServerConfig
from vbservice.src.filehandler import delete_directories_in, clear


class Test(TestCase):
    logging.basicConfig(
        level=logging.DEBUG, force=True,
        format="{levelname}::{filename}:{lineno}:\t{message}", style="{",
    )

    download_directory = 'tests/download'
    receive_directory = 'tests/testing-environment/tmp/server'
    send_directory = 'tests/testing-environment/tmp/client'

    server_vivado_user = 'vivado'
    server_port = 2025

    server_config = ServerConfig(
        server_port=server_port,
        num_workers=12
    )
    client_config = ClientConfig(
        server_port=server_port,
        server_ip_address='localhost',
        queue_user='Test',
    )

    server = BuildServer(server_config)
    server.general_config.is_test = True

    client = Client(client_config)
    client.general_config.is_test = True

    def test_usage(self):
        self.reset_testing_environment()

        def threaded_server(s: BuildServer):
            s.start()

        def threaded_client(c: Client):
            c.build(
                upload_dir='tests/build_dir',
                download_dir=self.download_directory,
                model_number='xc7s15ftgb196-2',
                only_bin_files=True
            )

        self.server_thread = threading.Thread(target=threaded_server, args=(self.server,))
        self.client_thread = threading.Thread(target=threaded_client, args=(self.client,))

        try:
            self.server_thread.start()
            self.client_thread.start()

            self.wait_until_files_are_downloaded(timeout_in_seconds=10)

            task_directory_exists = self.client.task_dir is not None
            self.assertTrue(task_directory_exists, "Task directory does not exist")

            result_dir = os.path.join(self.client.task_dir, 'result')
            self.compare_directories(dir1=result_dir, dir2=self.download_directory)

        except TimeoutError:
            self.fail("Timed out waiting for completion")
        except Exception as e:
            self.fail(f"Connection could not be established: {e}")
        finally:
            if self.server is not None:
                self.server.stop()

    def compare_directories(self, dir1, dir2):
        if not os.path.exists(dir1) or not os.path.exists(dir2):
            self.fail(f"One or both directories do not exist: {dir1}, {dir2}")

        if not os.path.isdir(dir1) or not os.path.isdir(dir2):
            self.fail(f"One or both paths are not directories: {dir1}, {dir2}")

        dir_comparison = filecmp.dircmp(dir1, dir2)

        if dir_comparison.diff_files or dir_comparison.left_only or dir_comparison.right_only:
            self.fail(f"Directories {dir1} and {dir2} are different.")

        for subdir in dir_comparison.common_dirs:
            self.compare_directories(os.path.join(dir1, subdir), os.path.join(dir2, subdir))

    def reset_testing_environment(self):
        clear(self.download_directory)
        delete_directories_in(self.receive_directory)
        delete_directories_in(self.send_directory)

    def wait_until_files_are_downloaded(self, timeout_in_seconds: int = None):
        start = time.time()
        while True:
            elapsed_seconds = time.time() - start
            download_directory_is_empty = len(os.listdir(self.download_directory)) == 0
            if timeout_in_seconds is not None and elapsed_seconds > timeout_in_seconds:
                raise TimeoutError
            elif download_directory_is_empty:
                time.sleep(1)
                continue
            else:
                return
