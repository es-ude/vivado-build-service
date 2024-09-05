import subprocess
import sys
from pathlib import Path

import tomli

from src.config import ServerConfig, GeneralConfig, default_general_config
from src.user_queue import UserQueue

from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import os

from src.threaded_tcp_handler import ThreadedTCPHandler, ThreadedTCPServer

logging.getLogger().setLevel(logging.INFO)


def load_server_config_from_toml(path: Path) -> ServerConfig:
    with open(path, 'rb') as f:
        config = tomli.load(f)
    return ServerConfig(
        server_vivado_user=config['server']['vivado_user'],
        server_port=int(config['server']['port']),
        tcl_script=os.path.abspath(config['paths']['tcl_script']),
        constraints=os.path.abspath(config['paths']['constraints']),
        bash_script=os.path.abspath(config['paths']['bash_script'] + 'unix.sh'),
        receive_folder=os.path.abspath(config['paths']['receive_folder']),
    )


class Server:
    def __init__(self, server_config: ServerConfig, general_config: GeneralConfig = None):
        self.event = threading.Event()
        self.server_config: ServerConfig = server_config
        if general_config:
            self.general_config = general_config
        else:
            self.general_config = default_general_config

        self.user_queue = UserQueue()
        self._server_loop_thread = threading.Thread(target=self._run_forever)
        self._server_loop_thread.daemon = True

        self._server_thread = None
        self._executor = ThreadPoolExecutor(max_workers=self.server_config.num_workers)

    def start(self):
        self._server_loop_thread.start()
        logging.info('server loop started.')
        server = ThreadedTCPServer(('localhost', self.server_config.server_port),
                                   ThreadedTCPHandler,
                                   self.user_queue,
                                   self.server_config,
                                   self.event,
                                   general_config=self.general_config
                                   )
        self._server_thread = threading.Thread(target=server.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()
        logging.info("Server is running.")
        logging.info("Waiting for connection...")

    def _run_forever(self):
        while True:
            if self.event.is_set():
                break

            task = self.user_queue.dequeue_task()
            self._executor.submit(execute, task, self.server_config, self.event)

    def stop(self):
        del self


def execute(task, server_config: ServerConfig, event):
    if event.is_set():
        return

    client_id = os.path.split(os.path.split(task)[0])[1]
    task_id = os.path.split(task)[1]
    result_dir = os.path.abspath(task + '/result')
    task_path = os.path.abspath(task)

    logging.info("Handling task for {}: Task nr. {}\n".format(client_id, task_id))

    _delete_report_lines_in_dir(os.path.abspath(task))

    bash_arguments = [
        server_config.server_vivado_user,
        server_config.tcl_script,
        task_path,
        result_dir,
        server_config.constraints
    ]

    _run_bash_script(server_config.bash_script, bash_arguments)

    # Insert data in DB - This part is not yet implemented

    logging.info("Task done for {}: Task nr. {} \n".format(client_id, task_id))


def _run_bash_script(bash_script: str, bash_arguments: list[str]):
    cygwin_path = ['C:\\cygwin64\\bin\\bash.exe', '-l']
    os_is_windows = sys.platform.startswith('win')

    try:
        if os_is_windows:
            subprocess.run(cygwin_path + [os.path.abspath(bash_script)] + bash_arguments,
                           capture_output=True, text=True, check=True)
        else:
            subprocess.run([os.path.abspath(bash_script)] + bash_arguments,
                           capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Something went wrong while executing bash script (Error Code: {e.returncode})\n{e.stderr}")


def _delete_report_lines_in_dir(directory: str):
    for (root, dirs, files) in os.walk(directory, topdown=True):
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            with open(file_path, 'r+') as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if 'report' not in line:
                        f.write(line)
                f.truncate()


def main():
    try:
        server_config = load_server_config_from_toml(Path("docs/default_server_config.toml"))
        server = Server(server_config)
        server.start()

    except Exception as e:
        logging.error("Something went wrong: {}".format(e))


if __name__ == '__main__':
    main()
