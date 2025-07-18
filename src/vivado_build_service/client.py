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
from shutil import copytree as copy_tree
import tomli

from .vtrunner.streamutil import join_streams
from .vtrunner.paths import ClientPaths, TMP_CLIENT_DIR
from .vtrunner.config import ClientConfig, GeneralConfig, default_general_config
from .vtrunner.filehandler import (
    make_personal_dir_and_get_task,
    get_filepaths,
    serialize,
    pack,
    unpack,
    deserialize,
)


class Client:
    def __init__(
        self, client_config: ClientConfig, general_config: GeneralConfig = None
    ):
        self.paths: ClientPaths = init_paths()
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
        with open(path, "rb") as f:
            config = tomli.load(f)
        config = ClientConfig(
            server_port=int(config["server"]["port"]),
            server_ip_address=config["server"]["ip_address"],
            queue_user=config["queue_user"],
        )
        return cls(config)

    def build(self, upload_dir, model_number, download_dir=None, only_bin_files=True):
        self.only_bin = only_bin_files
        self.model_number = model_number
        request, task_dir = self._prepare_request(
            upload_dir, self.client_config.queue_user
        )
        self.task_dir = task_dir
        data = join_streams(
            [
                self.client_config.queue_user.encode(),
                model_number.encode(),
                str(int(only_bin_files)).encode(),
                request,
            ],
            self.general_config.delimiter.encode(),
        )
        s = self._connect_with_socket()
        response = self._send_and_receive(s, data)
        result_dir = self._process_response(response)
        self.stop_loading_animation_event.set()

        bin_files = find_bin_files(result_dir)
        if not bin_files or len(bin_files) == 0:
            print("\nAn Error occurred. No bin file could be found.")
        for bf in bin_files:
            if "failure" in bf:
                print(
                    f"\nAn Error occurred. Read Vivado Run Log file for more information:"
                    f"\n{result_dir}/vivado_run.log"
                )
                print("failure.bin content:\n")
                time.sleep(1)
                with open(bf, "r") as f:
                    print(f.read())
        if download_dir:
            copy_tree(src=result_dir, dst=download_dir)
        s.close()

    def _forward_port(self):
        ssh_command = "ssh -Y -L {}:localhost:{} vivado@{}".format(
            self.client_config.server_port,
            self.client_config.server_port,
            self.client_config.server_ip_address,
        )
        subprocess.Popen(ssh_command, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _prepare_request(self, upload_directory: str, user: str) -> Tuple[str, str]:
        file_list = get_filepaths(upload_directory)
        task = make_personal_dir_and_get_task(
            user, self.paths.send_dir, self.model_number, self.only_bin
        )
        target_filepath = os.path.join(*[task.path, "build.zip"])
        pack(
            base_folder=upload_directory, origin=file_list, destination=target_filepath
        )

        return serialize(target_filepath), task.path

    def _send_and_receive(self, s: socket, data):
        loading_animation = threading.Thread(target=self._print_loading_animation)
        loading_animation.start()
        inputs, outputs = [s], [s]
        response = b""

        while inputs:
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs, 0.5
            )

            for s in writable:
                self._logger.info("Sending...\n")
                s.send(data)
                self._logger.info("Sent!")
                outputs.remove(s)

            for s in readable:
                chunk = s.recv(self.general_config.chunk_size)
                if not chunk:
                    self._logger.info("Closing...")
                    inputs.remove(s)
                    s.close()
                    break

                response += chunk

            for s in exceptional:
                self._logger.info("Error")
                inputs.remove(s)
                outputs.remove(s)
                break

        loading_animation.join(0.1)
        return response

    def _connect_with_socket(self) -> socket.socket | None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self._logger.info("Connecting...")
            ret = s.connect_ex(("localhost", self.client_config.server_port))

            if ret != 0:
                self._logger.info("Failed to connect!\n\n")
                raise ConnectionError

            self._logger.info("Connected!\n\n")
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
        print("", end="\n")

        while True:
            loading = "|/-\\"
            sys.stdout.write(
                "\rwaiting... {} (Time: {}:{}{})".format(
                    loading[index % len(loading)],
                    math.floor(elapsed_seconds) // 60,
                    "0" if math.floor(elapsed_seconds) % 60 < 10 else "",
                    math.floor(elapsed_seconds) % 60,
                )
            )
            sys.stdout.flush()
            time.sleep(0.5)
            elapsed_seconds += 0.5
            index += 1
            if self.stop_loading_animation_event.is_set():
                break

    def _process_response(self, data):
        result_dir = self.task_dir + "/result"
        zip_file = result_dir + "/result.zip"

        os.mkdir(result_dir)
        deserialize(data, zip_file)

        status = unpack(origin=zip_file, destination=result_dir)
        self._logger.info(status)

        os.remove(zip_file)

        return result_dir


def init_paths() -> ClientPaths:
    paths = ClientPaths(send_dir=TMP_CLIENT_DIR)
    return paths


def find_bin_files(directory):
    bin_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".bin"):
                bin_files.append(file)
    return bin_files


def parse_sys_argv(default_config_path, argv):
    username = argv[1]
    upload_data_folder = argv[2]
    model_number = argv[3]

    for arg in argv[4:]:
        if os.path.isdir(arg):
            download_data_folder = Path(arg)
            break
    else:
        download_data_folder = None

    for arg in argv[4:]:
        if arg.endswith(".toml"):
            config_path = Path(arg)
            break
    else:
        config_path = default_config_path

    if "-b" in sys.argv:
        only_bin_files = True
    else:
        only_bin_files = False

    return (
        username,
        upload_data_folder,
        model_number,
        download_data_folder,
        config_path,
        only_bin_files,
    )


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
        level=logging.DEBUG,
        force=True,
        format="{levelname}::{filename}:{lineno}:\t{message}",
        style="{",
    )
    argv = sys.argv
    if len(argv) not in (5, 6):
        print(main.__doc__)
        return
    default_config = Path("config/client_config.toml")
    (
        username,
        upload_data_folder,
        model_number,
        download_data_folder,
        config_path,
        only_bin_files,
    ) = parse_sys_argv(default_config, argv)
    client = Client.from_config(config_path)
    client.client_config.queue_user = username
    client.build(upload_data_folder, model_number, download_data_folder, only_bin_files)


if __name__ == "__main__":
    main()
