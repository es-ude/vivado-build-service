from src.filehandler import create_file
from docs.config import Config

import subprocess
import threading
import logging
import os

logging.getLogger().setLevel(logging.INFO)

config = Config().get()
task_is_finished = False


class UserQueue:
    def __init__(self):
        self.user_queues = {}

    def enqueue_task(self, task):
        client_id = task.split('/')[-2]

        if client_id not in self.user_queues:
            self.user_queues[client_id] = []

        self.user_queues[client_id].append(task)

    def dequeue_task(self):
        if not self.user_queues:
            return None

        next_user = next(iter(self.user_queues))

        if not self.user_queues[next_user]:
            del self.user_queues[next_user]
            return self.dequeue_task()
        
        task = self.user_queues[next_user].pop(0)
        return task


def execute(task):
    client_id = task.split('/')[-2]
    task_id = task.split('/')[-1]
    result_dir = task + '/result'
    bash_arguments = [config['username'], os.path.abspath(config['tcl script']), os.path.abspath(task), os.path.abspath(result_dir)]

    logging.info("Handling task for {}: Task nr. {} \n".format(client_id, task_id))
    
    subprocess.run(['./bash/local_autobuild_binfile_vivado2021.1.sh'] + bash_arguments)

    # Implement:
    # Insert data in DB

    create_file('completed.txt', result_dir)

    logging.info("Task done for {}: Task nr. {} \n".format(client_id, task_id))


user_queue = UserQueue()


def worker():
    while True:
        task = user_queue.dequeue_task()

        if task is None:
            continue

        execute(task)


thread = threading.Thread(target=worker)
thread.daemon = True
thread.start()
