import os
import time
import queue


class Task:
    def __init__(self, user: str, job_id: int, relative_path: str, only_bin: bool = True):
        self._user = user
        self._job_id = job_id
        self._only_bin = only_bin
        self._relative_path = relative_path

    def print(self):
        print(
            f"User: {self._user}\n"
            f"Job ID: {self._job_id}\n"
            f"Only .bin-files: {self._only_bin}\n"
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
    def bin_file_path(self):
        if self._only_bin:
            return 'output'
        else:
            return '*'


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
