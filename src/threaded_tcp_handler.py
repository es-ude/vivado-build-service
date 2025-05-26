import os
import logging
import shutil
import socketserver
import time
from pathlib import Path

from src.report_parser import create_toml_from_vivado_report
from src.user_queue import Task, UserQueue
from src.config import GeneralConfig
from src.streamutil import end_reached, remove_delimiter
from src.filehandler import (make_personal_dir_and_get_task, deserialize,
                             unpack, get_filepaths, pack, serialize, get_report_file_paths)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, request_handler_class, user_queue, server_config, event, general_config):
        socketserver.ThreadingMixIn.__init__(self)
        socketserver.TCPServer.__init__(self, server_address, request_handler_class)
        self.event = event
        self.user_queue = user_queue
        self.server_config = server_config
        self.general_config = general_config


class ThreadedTCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server: ThreadedTCPServer):
        super().__init__(request, client_address, server)
        self.server: ThreadedTCPServer = server

    def handle(self):
        user_queue: UserQueue = self.server.user_queue
        server_config = self.server.server_config
        general_config = self.server.general_config

        raw_data = self.get_request(self, general_config)
        task = Task.from_raw_request(raw_data, general_config, server_config.receive_folder)

        task_directory = task.path
        result_directory = task_directory + '/result'
        os.mkdir(result_directory)

        user_queue.enqueue_task(task)
        await_task_completion(directory=result_directory)

        response = prepare_response(result_directory)
        self.send(self, response, server_config)
        self.request.close()

    def send(self, tcp_handler, response, general_config: GeneralConfig):
        for i in range(0, len(response), self.server.general_config.chunk_size):
            chunk = response[i:i + self.server.general_config.chunk_size]
            tcp_handler.request.sendall(chunk)

    def shutdown(self):
        self.server.shutdown()
        logging.info("Server Shutdown")

    def get_request(self, tcp_handler, general_config: GeneralConfig):
        data = b''
        while True:
            chunk = tcp_handler.request.recv(self.server.general_config.chunk_size)
            data += chunk
            if (len(chunk) < self.server.general_config.chunk_size or
                    end_reached(chunk, self.server.general_config.delimiter)):
                break

        data = remove_delimiter(data, self.server.general_config.delimiter)
        return data

    def process_request(self, data, user, model_number, only_bin) -> Task:  # Server
        task = make_personal_dir_and_get_task(user, self.server.server_config.receive_folder, model_number, only_bin)
        task_dir = task.path
        filepath = '/'.join([task_dir, self.server.general_config.request_file])

        deserialize(data, filepath)

        status = unpack(filepath, task_dir)
        logging.info(status)

        os.remove(filepath)

        return task


def await_task_completion(directory):
    while True:
        bin_dir = os.path.join(directory, 'bin')
        if os.path.exists(bin_dir):
            found_bin = search_bin(bin_dir)
        else:
            found_bin = search_bin(directory)
        if found_bin:
            time.sleep(1)
            return


def search_bin(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.bin'):
            return True
    return False


def prepare_response(result_directory):
    reports = get_reports(result_directory)
    reports_directory = get_report_dir(result_directory)

    for report in reports:
        shutil.copy(report, reports_directory)

    create_toml_reports(result_directory)

    new_zip = os.path.join(result_directory, 'result.zip')
    all_files = get_filepaths(result_directory)
    pack(base_folder=result_directory, origin=all_files, destination=new_zip)

    return serialize(new_zip)


def get_reports(directory):
    files = get_filepaths(directory)
    reports = get_report_file_paths(files)
    return reports


def get_report_dir(directory):
    reports_directory = os.path.join(directory, 'reports')
    os.makedirs(reports_directory, exist_ok=True)
    return reports_directory


def create_toml_reports(result_dir):
    report_dir = os.path.join(result_dir, 'reports')
    toml_dir = os.path.join(result_dir, 'toml')
    os.makedirs(toml_dir, exist_ok=True)

    for root, dirs, files in os.walk(report_dir):
        for file in files:
            report_path = Path(root) / file
            toml_filepath = Path(toml_dir) / (get_filename(report_path) + '.toml')
            create_toml_from_vivado_report(report_path, toml_filepath)


def get_filename(filepath: Path) -> str:
    return filepath.name.split('.')[0]
