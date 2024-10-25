import time


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



