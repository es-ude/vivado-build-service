import threading
import time

from server import Server
from client import Client
from src.config import ClientConfig, ServerConfig

from unittest import TestCase


class Test(TestCase):
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

    def test(self):
        server = Server(self.server_config)
        server.general_config.is_test = True

        client = Client(self.client_config)
        client.general_config.is_test = True

        def threaded_server(s: Server):
            s.start()

        def threaded_client(c: Client):
            c.build(
                upload_dir='tests/build_dir',
                download_dir='tests/download',
                only_bin_files=True
            )

        server_thread = threading.Thread(target=threaded_server, args=(server,))
        client_thread = threading.Thread(target=threaded_client, args=(client,))

        server_thread.start()
        time.sleep(5)
        client_thread.start()

        while(True):
            ...

    def TearDown(self):
        ...


def compare_directories(dir1, dir2):
    ...
