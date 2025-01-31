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

from src.streamutil import join_streams
from src.config import ClientConfig, GeneralConfig, default_general_config
from src.report_parser import get_dict_from_vivado_report, get_toml_string, create_toml_from_vivado_report
from src.filehandler import make_personal_dir_and_get_task, get_filepaths, serialize, pack, unpack, deserialize, get_report_file_paths


class Client:
    def __init__(self, client_config: ClientConfig, general_config: GeneralConfig = None):
        self._logger = logging.getLogger(__name__)
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

    def build(self, upload_dir, model_number, download_dir=None, only_bin_files=True):
        self.only_bin = only_bin_files
        self.model_number = model_number
        request, task_dir = self._prepare_request(upload_dir, self.client_config.queue_user)
        self.task_dir = task_dir
        data = join_streams([
                self.client_config.queue_user.encode(),
                model_number.encode(),
                str(int(only_bin_files)).encode(),
                request
        ], self.general_config.delimiter.encode())
        s = self._connect_with_socket()
        response = self._send_and_receive(s, data)
        result_dir = self._process_response(response)

        report_dir = os.path.join(result_dir, 'reports')
        for report in os.listdir(report_dir):
            toml_filepath = os.path.join(result_dir, 'toml', report.split('.rpt')[0] + '.toml')
            create_toml_from_vivado_report(report, toml_filepath)

        if download_dir:
            copy_tree(src=result_dir, dst=download_dir)
        self.stop_loading_animation_event.set()
        s.close()


    def _forward_port(self):
        ssh_command = "ssh -Y -L {}:{}:{} {}@{}".format(
            self.client_config.server_port,
            'localhost',
            self.client_config.server_port,
            self.client_config.server_vivado_user,
            self.client_config.server_ip_address
        )
        subprocess.Popen(ssh_command, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _prepare_request(self, upload_directory: str, user: str) -> Tuple[str, str]:
        file_list = get_filepaths(upload_directory)
        task = make_personal_dir_and_get_task(user, self.client_config.send_dir, self.model_number, self.only_bin)
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
                self._logger.info('Sending...\n')
                s.send(data)
                self._logger.info('Sent!')
                outputs.remove(s)

            for s in readable:
                chunk = s.recv(self.general_config.chunk_size)
                if not chunk:
                    self._logger.info('Closing...')
                    inputs.remove(s)
                    s.close()
                    break

                response += chunk

            for s in exceptional:
                self._logger.info('Error')
                inputs.remove(s)
                outputs.remove(s)
                break

        loading_animation.join(.1)
        return response

    def _connect_with_socket(self) -> socket.socket | None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self._logger.info('Connecting...')
            ret = s.connect_ex(("localhost", self.client_config.server_port))

            if ret != 0:
                self._logger.info('Failed to connect!\n\n')
                raise ConnectionError

            self._logger.info('Connected!\n\n')
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

        status = unpack(origin=filepath, destination=result_dir)
        self._logger.info(status)

        os.remove(filepath)

        return result_dir


def parse_sys_argv(default_config_path):
    username = sys.argv[1]
    upload_data_folder = sys.argv[2]
    model_number = sys.argv[3]

    for arg in sys.argv[4:]:
        if os.path.isdir(arg):
            download_data_folder = Path(arg)
            break
    else:
        download_data_folder = None

    for arg in sys.argv[4:]:
        if arg.endswith(".toml"):
            config_path = Path(arg)
            break
    else:
        config_path = default_config_path

    if '-b' in sys.argv:
        only_bin_files = True
    else:
        only_bin_files = False

    return username, upload_data_folder, model_number, download_data_folder, config_path, only_bin_files


def main():
    """
    A correct call from the command line looks like this:
        client.py {username} {upload_dir} {model_number} {download_dir} {config_path} {-b}

    username        User that connects to the server
    upload_dir      Directory where the build files are located
    model_number    Model number of the FPGA that is being used
    download_dir    Directory where output files should be downloaded
    config_path     Path to a client_config.toml file
    -b              If flag is present, only bin files will be downloaded

    Arguments download_dir, config_path and -b are optional.
    """
    logging.basicConfig(
        level=logging.DEBUG, force=True,
        format="{levelname}::{filename}:{lineno}:\t{message}", style="{",
    )
    default_config = Path("config/client_config.toml")
    username, upload_data_folder, model_number, download_data_folder, config_path, only_bin_files = parse_sys_argv(default_config)
    client = Client.from_config(config_path)
    client.client_config.queue_user = username
    client.build(upload_data_folder, model_number, download_data_folder, only_bin_files)


if __name__ == '__main__':
    main()
