import os
import sys
import logging
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import tomli

from .user_queue import UserQueue, Task
from .threaded_tcp_handler import ThreadedTCPHandler, ThreadedTCPServer
from .config import ServerConfig, GeneralConfig, default_general_config

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


class BuildServer:
    def __init__(self, server_config: ServerConfig, general_config: GeneralConfig = None):
        self.server_config: ServerConfig = server_config
        if general_config:
            self.general_config = general_config
        else:
            self.general_config = default_general_config

        self.user_queue = UserQueue()

        self.shutdown_event = threading.Event()
        self._server_loop_thread = threading.Thread(target=self._run_forever, args=(self.shutdown_event,))
        self._server_loop_thread.daemon = True

        self._server_thread = None
        self._executor = ThreadPoolExecutor(max_workers=self.server_config.num_workers)

    def start(self):
        self._server_loop_thread.start()
        logging.info(':Server: Server loop started.')
        self.tcp_server = ThreadedTCPServer(('localhost', self.server_config.server_port),
                                            ThreadedTCPHandler,
                                            self.user_queue,
                                            self.server_config,
                                            self.shutdown_event,
                                            general_config=self.general_config
                                            )
        self._server_thread = threading.Thread(target=self.tcp_server.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()
        logging.info(":Server: Server is running.")
        logging.info(":Server: Waiting for connection...\n")

    def _run_forever(self, shutdown_event: threading.Event):
        while True:
            if shutdown_event.is_set():
                break

            task = self.user_queue.dequeue_task()

            if task is not None:
                self._executor.submit(execute, task, self.server_config, shutdown_event)

    def stop(self):
        print('')
        logging.info(":Server: Shutting down...")
        self.tcp_server.shutdown()
        self.shutdown_event.set()

        self._executor.shutdown(wait=True)

        logging.info(":Server: Shutdown complete.")


def execute(task: Task, server_config: ServerConfig, event):
    if event.is_set():
        return

    logging.info(":Server: Handling task for {}: Task nr. {}".format(task.user, task.job_id))

    _delete_report_lines_in_dir(os.path.abspath(task.path()))

    task_path = task.abspath
    result_dir = os.path.join(task_path, 'result')

    bash_arguments = [
        server_config.server_vivado_user,
        server_config.tcl_script,
        task_path,
        result_dir,
        server_config.constraints,
        task.bin_file_path
    ]
    logging.info(":Server: Running Bash Script\n")
    _run_bash_script(server_config.bash_script, bash_arguments)

    # Insert data in (rudimentary) DB - This part is not yet implemented

    logging.info(":Server: Task done for {}: Task nr. {} \n".format(task.user, task.job_id))


def _run_bash_script(bash_script: str, bash_arguments: list[str]):
    os_is_windows = sys.platform.startswith('win')
    cygwin_path = ['C:\\cygwin64\\bin\\bash.exe', '-l']
    bash_script_path = [os.path.abspath(bash_script)]

    if os_is_windows:
        bash_script_path = cygwin_path + bash_script_path

    try:
        subprocess.run(bash_script_path + bash_arguments,
                       stdout=None, stderr=None, check=True)
    #                   capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f":Server: Something went wrong while executing bash script (Error Code: {e.returncode})\n{e.stderr}")
    except Exception as e:
        logging.error(f":Server: Something went wrong while executing bash script:\n{e}")


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
    server_config = load_server_config_from_toml(Path("../config/default_server_config.toml"))
    server = BuildServer(server_config)
    server.start()


if __name__ == '__main__':
    main()
