import os
import shutil
import threading
import time

from src.buildserver import BuildServer
from src.client import Client
from src.config import ClientConfig, ServerConfig

from unittest import TestCase


class Test(TestCase):
    download_directory = 'tests/download'
    testing_environment = ['tmp/server/Test', 'tmp/client/Test']

    server_vivado_user = 'dominik'
    server_port = 2025

    server_config = ServerConfig(
        server_vivado_user=server_vivado_user,
        server_port=server_port,
        tcl_script='scripts/tcl/create_project_full_run.tcl',
        constraints='scripts/constraints/env5_config.xdc',
        bash_script='scripts/bash/testing.sh',
        receive_folder='tmp/server',
        num_workers=12
    )
    client_config = ClientConfig(
        server_vivado_user=server_vivado_user,
        server_port=server_port,
        server_ip_address='localhost',
        queue_user='Test',
        send_dir='tmp/client',
    )

    server = BuildServer(server_config)
    server.general_config.is_test = True

    client = Client(client_config)
    client.general_config.is_test = True

    def test_usage(self):
        reset_testing_environment(self.testing_environment, self.download_directory)

        def threaded_server(s: BuildServer):
            s.start()

        def threaded_client(c: Client):
            c.build(
                upload_dir='tests/build_dir',
                download_dir=self.download_directory,
                only_bin_files=True
            )

        self.server_thread = threading.Thread(target=threaded_server, args=(self.server,))
        self.client_thread = threading.Thread(target=threaded_client, args=(self.client,))

        # try
        self.server_thread.start()
        self.client_thread.start()

        wait_until_files_are_downloaded(self.download_directory, timeout_in_seconds=10)

        task_directory_exists = self.client.task_dir is not None
        self.assertTrue(task_directory_exists, "Task directory does not exist")

        self.assertTrue(
            expr=compare_directories(dir1=self.client.task_dir, dir2=self.download_directory),
            msg="Files are not equal")

        if self.server is not None:
            self.server.stop()

        reset_testing_environment(self.testing_environment, self.download_directory)


"""
        try:
            self.server_thread.start()
            self.client_thread.start()

            wait_until_files_are_downloaded(self.download_directory, timeout_in_seconds=10)

            task_directory_exists = self.client.task_dir is not None
            self.assertTrue(task_directory_exists, "Task directory does not exist")

            self.assertTrue(
                expr=compare_directories(dir1=self.client.task_dir, dir2=self.download_directory),
                msg="Files are not equal")

        except TimeoutError:
            self.fail("Timed out waiting for completion")
        except Exception as e:
            self.fail(f"Connection could not be established: {e}")
        finally:
            if self.server is not None:
                self.server.stop()
            reset_testing_environment(self.testing_environment, self.download_directory)
"""


def reset_testing_environment(testing_env: list[str], download_dir: str):
    for folder in testing_env + [download_dir]:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
    for directory in testing_env:
        if os.path.exists(directory):
            os.rmdir(directory)


def compare_directories(dir1, dir2):
    ...
    return True


def wait_until_files_are_downloaded(download_directory, timeout_in_seconds: int = None):
    start = time.time()
    while True:
        elapsed_seconds = time.time() - start
        download_directory_is_empty = len(os.listdir(download_directory)) == 0
        if timeout_in_seconds is not None and elapsed_seconds > timeout_in_seconds:
            raise TimeoutError
        elif download_directory_is_empty:
            time.sleep(1)
            continue
        else:
            return
