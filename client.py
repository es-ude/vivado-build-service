import os
import sys
import math
import time
import socket
import select
import logging
import threading
import subprocess
from pathlib import Path
from typing import Tuple
from contextlib import closing
from distutils.dir_util import copy_tree

import tomli

from src.config import ClientConfig, GeneralConfig, default_general_config
from src.filehandler import make_personal_dir_and_get_task, get_filepaths, serialize, pack, unpack, deserialize
from src.streamutil import join_streams

logging.getLogger().setLevel(logging.INFO)


class Client:
    def __init__(self, client_config: ClientConfig, general_config: GeneralConfig = None):
        self.task_dir = None
        self.client_config = client_config
        if general_config:
            self.general_config = general_config
        else:
            self.general_config = default_general_config
        if not self.general_config.is_test:
            self._forward_port()
        self.stop_loading_animation_event = threading.Event()

    @classmethod
    def from_config(cls, path: Path):
        with open(path, 'rb') as f:
            config = tomli.load(f)
        config = ClientConfig(
            server_vivado_user=config['server']['vivado_user'],
            server_port=int(config['server']['port']),
            server_ip_address=config['server']['ip_address'],
            queue_user=config['queue_user'],
            send_dir=config['paths']['send_dir']
        )
        return cls(config)

    def _forward_port(self):
        ssh_command = "ssh -Y -L {}:{}:{} {}@{}".format(
            self.client_config.server_port,
            'localhost',
            self.client_config.server_port,
            self.client_config.server_vivado_user,
            self.client_config.server_ip_address
        )
        print(ssh_command)
        subprocess.Popen(ssh_command, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def build(self, upload_dir, download_dir=None, only_bin_files=True):
        self.only_bin = only_bin_files
        request, task_dir = self._prepare_request(upload_dir, self.client_config.queue_user)
        self.task_dir = task_dir
        data = join_streams([
                self.client_config.queue_user.encode(),
                str(int(only_bin_files)).encode(),
                request
        ], self.general_config.delimiter.encode())
        s = self._connect_with_socket()
        response = self._send_and_receive(s, data)
        result_dir = self._process_response(response)
        if download_dir:
            copy_tree(src=result_dir, dst=download_dir)
        self.stop_loading_animation_event.set()
        s.close()

    def _prepare_request(self, upload_directory: str, user: str) -> Tuple[str, str]:
        file_list = get_filepaths(upload_directory)
        task = make_personal_dir_and_get_task(user, self.client_config.send_dir, self.only_bin)
        target_filepath = os.path.join(*[task.path, self.general_config.request_file])
        pack(base_folder=upload_directory, origin=file_list, destination=target_filepath)

        return serialize(target_filepath), task.path

    def _send_and_receive(self, s: socket, data):
        loading_animation = threading.Thread(target=self._print_loading_animation)
        loading_animation.start()
        inputs, outputs = [s], [s]
        response = b''

        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.5)

            for s in writable:
                print('\n')
                logging.info(':Client: Sending...\n')
                s.send(data)
                logging.info(':Client: Sent!')
                outputs.remove(s)

            for s in readable:
                chunk = s.recv(self.general_config.chunk_size)
                if not chunk:
                    logging.info(':Client: Closing...')
                    inputs.remove(s)
                    s.close()
                    break

                response += chunk

            for s in exceptional:
                logging.info(':Client: Error')
                inputs.remove(s)
                outputs.remove(s)
                break

        loading_animation.join(.1)
        return response

    def _connect_with_socket(self) -> socket.socket | None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            logging.info(':Client: Connecting...')
            ret = s.connect_ex(("localhost", self.client_config.server_port))

            if ret != 0:
                logging.info(':Client: Failed to connect!\n')
                raise ConnectionError

            logging.info(':Client: Connected!\n')
            s.setblocking(False)
            return s

        except Exception as e:
            print(e)

    def _check_socket(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            return sock.connect_ex(("localhost", self.client_config.server_port)) == 0

    def _print_loading_animation(self):
        index = 0
        elapsed_seconds = 0
        print('', end='\n')

        while True:
            loading = "|/-\\"
            sys.stdout.write("\rwaiting... {} (Time: {}:{}{})".format(
                loading[index % len(loading)],
                math.floor(elapsed_seconds) // 60,
                "0" if math.floor(elapsed_seconds) % 60 < 10 else "",
                math.floor(elapsed_seconds) % 60
            ))
            sys.stdout.flush()
            time.sleep(.5)
            elapsed_seconds += .5
            index += 1
            if self.stop_loading_animation_event.is_set():
                break

    def _process_response(self, data):
        result_dir = self.task_dir + '/result'
        filepath = result_dir + '/result.zip'

        os.mkdir(result_dir)
        deserialize(data, filepath)
        unpack(origin=filepath, destination=result_dir)
        os.remove(filepath)

        return result_dir


def main(config_path: Path = Path("config/client_config.toml")):
    client = Client.from_config(config_path)

    client.client_config.queue_user = sys.argv[1]
    upload_data_folder = sys.argv[2]
    try:
        download_data_folder = sys.argv[3]
    except IndexError:
        download_data_folder = None

    client.build(upload_data_folder, download_data_folder)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 0:
        config_path = Path(sys.argv[1])
        main(config_path)
    else:
        main()
