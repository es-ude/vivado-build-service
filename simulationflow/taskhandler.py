import threading

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
    print("Executing Task '{}'".format(task), end='\n\n')
    # Exec Bash Script
    # Await Response
    # Insert in DB
    pass

user_queue = UserQueue()

def worker():
    while True:
        task = user_queue.dequeue_task()

        if task is None:
            continue

        client_id = task.split('/')[-2]
        task_id = task.split('/')[-1]

        print("Handling task for {}: Task nr. {}".format(client_id, task_id), end='\n\n')
        execute(task)

threading.Thread(target=worker, daemon=True).start()
