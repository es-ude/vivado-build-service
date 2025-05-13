import os
import sys
import logging
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import tomli

from src.user_queue import UserQueue, Task
from src.reset import move_log_and_jou_files
from src.autobuild import run_vivado_autobuild
from src.filehandler import configure_bash_scripts
from src.threaded_tcp_handler import ThreadedTCPHandler, ThreadedTCPServer
from src.config import ServerConfig, GeneralConfig, default_general_config


class BuildServer:
    tcp_server: ThreadedTCPServer

    def __init__(self, server_config: ServerConfig, general_config: GeneralConfig = None):
        self._logger = logging.getLogger(__name__)
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
        bash_dir = os.path.dirname(self.server_config.bash_script)
        configure_bash_scripts(bash_dir)

    def start(self):
        self._server_loop_thread.start()
        self._logger.info('Server loop started.')
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
        self._logger.info("Server is running.")
        self._logger.info("Waiting for connection...\n")
        self._server_thread.join()

    def _run_forever(self, shutdown_event: threading.Event):
        while True:
            if shutdown_event.is_set():
                break
            task: Task = self.user_queue.dequeue_task()
            if task is not None:
                self._executor.submit(execute, task, self.server_config, shutdown_event)

    def stop(self):
        self._logger.info("Shutting down...")
        self.tcp_server.shutdown()
        self.shutdown_event.set()
        self._executor.shutdown(wait=True)
        self._logger.info("Shutdown complete.")


def execute(task: Task, server_config: ServerConfig, event):
    logger = logging.getLogger(__name__)
    if event.is_set():
        return

    logger.info("Handling task for {}: Task nr. {}\n".format(task.user, task.job_id))
    task.print()

    delete_report_lines_in_dir(os.path.abspath(task.path))
    task_path = task.abspath
    result_dir = os.path.join(task_path, 'result')

    logger.info("Running Vivado\n")
    run_vivado_autobuild(
        server_config.server_vivado_user,
        server_config.tcl_script,
        task_path,
        result_dir,
        server_config.constraints,
        task.bin_file_path,
        task.model_number
    )

    move_log_and_jou_files(origin=".", destination="log")
    logger.info("Task done for {}: Task nr. {} \n".format(task.user, task.job_id))


def delete_report_lines_in_dir(directory: str):
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


def main():
    default_config_path = Path("config/server_config.toml")

    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    else:
        config_path = default_config_path

    logging.basicConfig(
        level=logging.DEBUG, force=True,
        format="{levelname}::{filename}:{lineno}:\t{message}", style="{",
    )

    server_config = load_server_config_from_toml(config_path)
    server = BuildServer(server_config)
    server.start()


if __name__ == '__main__':
    main()
