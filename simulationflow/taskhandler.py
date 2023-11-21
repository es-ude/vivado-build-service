from docs.config import Config
from simulationflow.filehandler import remove, prepare_request
import subprocess
import threading

config = Config().get()

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
    arguments = [config['username'], config['ip address'], task]

    print("Handling task for {}: Task nr. {}".format(client_id, task_id), end='\n\n')
    
    subprocess.run(['C:/Windows/System32/wsl.exe', './bash/test.sh'])
    # subprocess.run(['./bash/local_autobuild_binfile_vivado2021.1.sh'] + arguments)

    data = prepare_request(['/home/' + config['username'] + '/.autobuild/output'], client_id)

    # Implement:
    # Send *bin file and tcl script back to client
    # Insert data in DB

    print("Task done for {}: Task nr. {}".format(client_id, task_id), end='\n\n')
    remove(task)

user_queue = UserQueue()

def worker():
    while True:
        task = user_queue.dequeue_task()

        if task is None:
            continue

        execute(task)

threading.Thread(target=worker, daemon=True).start()
