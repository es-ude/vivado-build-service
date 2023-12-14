from docs.config import Config
from simulationflow.filehandler import create_file
import subprocess
import threading

config = Config().get()
task_is_finished = False

class UserQueue:
    def __init__(self):
        self.user_queues = {}
    
    def enqueue_task(self, task):
        print("TEST 2")
        
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
    print("TEST 1")
    
    client_id = task.split('/')[-2]
    task_id = task.split('/')[-1]
    result_dir = task + '/result'
    bash_arguments = [config['username'], config['ip address'], task, result_dir]

    print("Handling task for {}: Task nr. {}".format(client_id, task_id), end='\n\n')
    
    subprocess.run(['C:/Windows/System32/wsl.exe', './bash/test.sh'])
    create_file('completed.txt', result_dir)
    # subprocess.run(['./bash/local_autobuild_binfile_vivado2021.1.sh'] + bash_arguments)

    # Implement:
    # Insert data in DB

    print("Task done for {}: Task nr. {}".format(client_id, task_id), end='\n\n')

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
