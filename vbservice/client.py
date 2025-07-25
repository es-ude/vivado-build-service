import os
import shutil
import sys
import math
import time
import socket
import select
import logging
import platform
import threading
import subprocess
from pathlib import Path
from contextlib import closing

import tomli

from vbservice.src.streamutil import join_streams
from vbservice.config import ClientConfig, GeneralConfig, default_general_config
from vbservice.src.filehandler import (
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
        self._logger = logging.getLogger(__name__)

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

    def build(self, upload_dir, model_number, download_dir, only_bin_files=True):
        self.download_dir = make_unique_dir(download_dir)
        request = self._prepare_request(upload_dir)

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
        s.close()

    def _forward_port(self):
        ssh_command = "ssh -Y -L {}:localhost:{} vivado@{}".format(
            self.client_config.server_port,
            self.client_config.server_port,
            self.client_config.server_ip_address,
        )
        if platform_is("Linux"):
            terminal = _get_linux_terminal()
            if terminal:
                subprocess.Popen([terminal, "-e", ssh_command])
            else:
                raise EnvironmentError("No supported terminal emulator found on this system.")
        elif platform_is("Windows"):
            subprocess.Popen(ssh_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif platform_is("macOS"):
            osa_command = f'''
            tell application "Terminal"
                do script "{ssh_command}"
                activate
            end tell
            '''
            subprocess.Popen(["osascript", "-e", osa_command])

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

    def _prepare_request(self, upload_directory: str) -> str:
        file_list = get_filepaths(upload_directory)
        target_filepath = os.path.join(upload_directory, "build.zip")
        pack(
            base_folder=upload_directory, origin=file_list, destination=target_filepath
        )
        request = serialize(target_filepath)
        unpack(target_filepath, self.download_dir)
        os.remove(target_filepath)
        return request

    def _process_response(self, data):
        result_dir = self.download_dir + "/result"
        zip_file = result_dir + "/result.zip"

        os.mkdir(result_dir)
        deserialize(data, zip_file)

        status = unpack(origin=zip_file, destination=result_dir)
        self._logger.info(status)

        os.remove(zip_file)

        return result_dir


def platform_is(system: str) -> bool:
    if platform.system == system:
        return True
    if system == "macOS" and platform.system == "Darwin":
        return True
    return False


def _get_linux_terminal():
    terminals = [
        "x-terminal-emulator",
        "gnome-terminal",
        "konsole",
        "xfce4-terminal",
        "lxterminal",
        "xterm",
        "terminator",
        "mate-terminal"
    ]
    for term in terminals:
        if shutil.which(term):
            return term
    return None


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


def make_unique_dir(download_dir):
    files = os.listdir(download_dir)
    job_numbers = [0]
    for file in files:
        if file.startswith("project_"):
            job_numbers.append(int(file.split("_")[-1]))
    job_number = max(job_numbers) + 1
    directory = os.path.join(download_dir, f"project_{str(job_number)}")
    os.makedirs(directory, exist_ok=True)
    return directory


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
