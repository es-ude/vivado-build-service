from . import config

import subprocess
import logging
import sys
import os

logging.getLogger().setLevel(logging.INFO)

global bash_script
tcl_script = os.path.abspath(config['tcl script'])
constraints = os.path.abspath(config['constraints'])
bash_script = [os.path.abspath(config['bash script'] + 'unix.sh')]
vnc_user = config['username']

task_is_finished = False
os_is_windows = sys.platform.startswith('win')
cygwin_path = ['C:\\cygwin64\\bin\\bash.exe', '-l'] 

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


def execute(task, event, testing=False):
    global bash_script

    if event.is_set():
        return
    
    client_id = os.path.split(os.path.split(task)[0])[1]
    task_id = os.path.split(task)[1]
    result_dir = os.path.abspath(task + '/result')
    task_path = os.path.abspath(task)

    if testing:
        bash_script = [os.path.abspath(config['test bash script'])]

    logging.info("Handling task for {}: Task nr. {}\n".format(client_id, task_id))

    delete_report_lines_in_dir(os.path.abspath(task))

    bash_arguments = [vnc_user, tcl_script, task_path, result_dir, constraints]

    try:
        if os_is_windows:
            out = subprocess.run(cygwin_path + bash_script + bash_arguments, 
                                 capture_output=True, text=True, check=True)
        else:
            out = subprocess.run(bash_script + bash_arguments,
                                 capture_output=True, text=True, check=True)
    except Exception as e:
        logging.error(e)
        return

    # Insert data in DB - This part is not yet implemented

    logging.info("Task done for {}: Task nr. {} \n".format(client_id, task_id))


def delete_report_lines_in_dir(dir: str):
    for (root, dirs, files) in os.walk(dir, topdown=True):
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            try:
                with open(file_path, 'r+') as f:
                    lines = f.readlines()
                    f.seek(0)
                    for line in lines:
                        if 'report' not in line:
                            f.write(line)
                    f.truncate()

            except Exception as e:
                logging.error(f"\nError deleting report lines: {e}")
                continue
