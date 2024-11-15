import os
import time


class Task:
    def __init__(self, user: str, job_id: int, relative_path: str, only_bin: bool = True):
        self._user = user
        self._job_id = job_id
        self._only_bin = only_bin
        self._relative_path = relative_path

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
        self.user_queues = {}  # Stores tasks for each user
        self.next_users = []  # Keeps track of the order in which users are processed

    def enqueue_task(self, task):
        # We use the task's user as the key, not extracting from the path
        client_id = task.user
        if client_id not in self.next_users:
            self.next_users.append(client_id)

        if client_id not in self.user_queues:
            self.user_queues[client_id] = []

        # Add the task to the user's queue
        self.user_queues[client_id].append(task)

    def dequeue_task(self):
        if len(self.user_queues) == 0:
            # If no tasks are available, wait for a while before checking again
            time.sleep(0.1)
            return None

        # Pop the next user from the queue (FIFO order)
        next_user = self.next_users.pop(0)

        # Pop the first task from the user's queue
        task = self.user_queues[next_user].pop(0)

        # If the user's queue is empty, remove them from the main user queue
        if len(self.user_queues[next_user]) == 0:
            del self.user_queues[next_user]
        else:
            # Otherwise, re-add the user to the list to continue processing their tasks later
            self.next_users.append(next_user)

        return task


"""
class UserQueue:
    def __init__(self):
        self.user_queues = {}
        self.next_users = list()

    def enqueue_task(self, task):
        client_id = task.split('/')[-2]
        if client_id not in self.next_users:
            self.next_users.append(client_id)

        if client_id not in self.user_queues:
            self.user_queues[client_id] = list()

        self.user_queues[client_id].append(task)

    def dequeue_task(self):
        if len(self.user_queues) == 0:
            time.sleep(0.1)
            return

        next_user = self.next_users.pop(0)

        task = self.user_queues[next_user].pop(0)
        if len(self.user_queues[next_user]) == 0:
            del self.user_queues[next_user]
        else:
            self.next_users.append(next_user)
        return task
"""
