import math
import shutil
import threading
import time

from src.config import ClientConfig, GeneralConfig, default_general_config
from src.filehandler import make_personal_dir, get_filepaths, serialize, pack, unpack, deserialize
from src.streamutil import join_streams

from contextlib import closing
from pathlib import Path
from typing import Tuple
import os
import tomli
import subprocess
import logging
import socket
import select
import sys

logging.getLogger().setLevel(logging.INFO)


def load_client_config_from_toml(path: Path) -> ClientConfig:
    with open(path, 'rb') as f:
        config = tomli.load(f)
    return ClientConfig(
        server_vivado_user=config['server']['vivado_user'],
        server_port=int(config['server']['port']),
        server_ip_address=config['server']['ip_address'],
        queue_user=config['user']['queue_user'],
        send_dir=config['paths']['send_dir']
    )


class Client:
    def __init__(self, client_config: ClientConfig, general_config: GeneralConfig = None):
        self.client_config = client_config
        if general_config:
            self.general_config = general_config
        else:
            self.general_config = default_general_config
        if not self.general_config.is_test:
            self._forward_port()

    def _forward_port(self):
        if check_socket:
            subprocess.Popen("ssh -Y -L {}:{}:{} {}@{}".format(
                self.client_config.server_port,
                'localhost',
                self.client_config.server_port,
                self.client_config.server_vivado_user,
                self.client_config.server_ip_address
            ), creationflags=subprocess.CREATE_NEW_CONSOLE)

    def build(self, upload_dir, download_dir=None, only_bin_files=True):
        request, task_dir = self._prepare_request(upload_dir, self.client_config.queue_user)
        data = join_streams([
                self.client_config.queue_user.encode(),
                str(int(only_bin_files)).encode(),
                request
        ], self.general_config.delimiter.encode())
        s = connect_with_socket(self.client_config.server_ip_address, self.client_config.server_port)
        response = self._send_and_receive(s, data)
        result_dir = process_response(response, task_dir)
        if download_dir:
            shutil.copy(src=result_dir, dst=download_dir)

    def _prepare_request(self, upload_directory: str, user: str) -> Tuple[str, str]:
        file_list = get_filepaths(upload_directory)
        task_dir = make_personal_dir(user, self.client_config.send_dir)
        target_filepath = os.path.join(*[task_dir, self.general_config.request_file])
        pack(base_folder=upload_directory, origin=file_list, destination=target_filepath)

        return serialize(target_filepath), task_dir

    def _send_and_receive(self, s: socket, data):
        loading_animation = threading.Thread(target=print_loading_animation)
        loading_animation.start()
        inputs, outputs = [s], [s]
        response = b''

        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.5)

            for s in writable:
                logging.info('sending...')
                s.send(data)
                logging.info('sent!\n')
                outputs.remove(s)

            for s in readable:
                chunk = s.recv(self.general_config.chunk_size)
                if not chunk:
                    logging.info('\nclosing...\n')
                    inputs.remove(s)
                    s.close()
                    break

                response += chunk

            for s in exceptional:
                logging.info('\nerror')
                inputs.remove(s)
                outputs.remove(s)
                break

        loading_animation.join(.1)
        return response


def connect_with_socket(host, port) -> socket.socket | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logging.info('connecting...')
        ret = s.connect_ex((host, port))

        if ret != 0:
            logging.info('failed to connect!\n')
            return

        logging.info('connected!\n')
        s.setblocking(False)

        return s
    except Exception as e:
        print(e)


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0


def print_loading_animation():
    index = 0
    elapsed_seconds = 0
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


def process_response(data, task_dir):
    result_dir = task_dir + '/result'
    filepath = result_dir + '/result.zip'

    os.mkdir(result_dir)
    deserialize(data, filepath)
    unpack(origin=filepath, destination=result_dir)
    os.remove(filepath)

    return result_dir


def main():
    try:
        client_config = load_client_config_from_toml(Path("docs/default_client_config.toml"))
        client_config.queue_user = sys.argv[1]
        client_config.upload_data_folder = sys.argv[2]
        try:
            client_config.download_data_folder = sys.argv[3]
        except IndexError:
            client_config.download_data_folder = None

        client = Client(client_config)
        client.build(client_config.upload_data_folder, client_config.download_data_folder)

    except Exception as e:
        logging.error(f'Something went wrong: {e}')


if __name__ == '__main__':
    main()
