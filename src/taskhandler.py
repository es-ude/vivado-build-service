from docs.config import Config

import subprocess
import threading
import logging
import os

logging.getLogger().setLevel(logging.INFO)

config = Config().get()
tcl_script = os.path.abspath(config['tcl script'])
constraints = os.path.abspath(config['constraints'])
bash_script = os.path.abspath(config['bash script'] + 'unix.sh')

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
    result_dir = os.path.abspath(task + '/result')
    task_path = os.path.abspath(task)

    logging.info("Handling task for {}: Task nr. {} \n".format(client_id, task_id))

    delete_report_lines_in_dir(os.path.abspath(task))

    bash_arguments = [client_id, tcl_script, task_path, result_dir, constraints]
    out = subprocess.run([bash_script] + bash_arguments, capture_output=True, text=True)
    
    if out.returncode !=0:
        logging.error(f"Error executing autobuild script: {out.stderr}")

    # Implement:
    # Insert data in DB

    logging.info("Task done for {}: Task nr. {} \n".format(client_id, task_id))


user_queue = UserQueue()

def delete_report_lines_in_dir(dir: str):
    for (root, dirs, files) in os.walk(dir, topdown=True):
        for file in files:
            file_path = os.path.join(root, file)
            subprocess.run(["sed", '-i', '/report/d', os.path.abspath(file_path)])


def worker():
    while True:
        task = user_queue.dequeue_task()

        if task is None:
            continue

        execute(task)


thread = threading.Thread(target=worker)
thread.daemon = True
thread.start()
