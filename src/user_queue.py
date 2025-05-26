import logging
import os
import time
import queue

from src.filehandler import make_personal_dir_and_get_task, deserialize, unpack
from src.streamutil import split_stream, remove_delimiter


class Task:
    def __init__(self, user: str, job_id: int, relative_path: str, model_number: str, only_bin: bool = True):
        self._user = user
        self._job_id = job_id
        self._model_number = model_number
        self._only_bin = only_bin
        self._relative_path = relative_path

    def print(self):
        print(
            f"Task:\n"
            f"\tUser: {self._user}\n"
            f"\tJob ID: {self._job_id}\n"
            f"\tModel Number: {self._model_number}\n"
            f"\tOnly .bin-files: {self._only_bin}\n"
        )

    @property
    def path(self):
        return os.path.join(self._relative_path, self._user, str(self._job_id))

    @property
    def abspath(self):
        return os.path.abspath(self.path)

    @property
    def user(self):
        return self._user

    @property
    def job_id(self):
        return self._job_id

    @property
    def model_number(self):
        return self._model_number

    @property
    def bin_file_path(self):
        if self._only_bin:
            return '/bin'
        else:
            return ''

    @classmethod
    def from_raw_request(cls, raw_data: bytes, general_config, receive_folder: str) -> "Task":
        client_username, stream = split_stream(raw_data, general_config.delimiter.encode())
        model_number, stream = split_stream(stream, general_config.delimiter.encode())
        only_bin_file, stream = split_stream(stream, general_config.delimiter.encode())
        only_bin_file = bool(int(only_bin_file))

        data = remove_delimiter(stream, general_config.delimiter)

        task = make_personal_dir_and_get_task(client_username, receive_folder, model_number, only_bin_file)
        filepath = os.path.join(task.path, general_config.request_file)

        deserialize(data, filepath)
        status = unpack(filepath, task.path)
        logging.info(status)

        os.remove(filepath)
        return task


class UserQueue:
    def __init__(self):
        self.user_queues = {}
        self.next_users = queue.Queue()

    def enqueue_task(self, task: Task):
        client_id = task.user

        if client_id not in self.user_queues:
            self.user_queues[client_id] = queue.Queue()
            self.next_users.put(client_id)

        self.user_queues[client_id].put(task)

    def dequeue_task(self) -> Task | None:
        if not self.next_users.empty():
            next_user = self.next_users.get()

            if not self.user_queues[next_user].empty():
                task = self.user_queues[next_user].get()

                if self.user_queues[next_user].empty():
                    del self.user_queues[next_user]
                else:
                    self.next_users.put(next_user)

                return task
        time.sleep(0.1)
        return None
