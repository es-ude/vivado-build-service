from docs.config import Config
from simulationflow.filehandler import clear

config = Config().get()
send_dir, receive_dir = config['send'], config['receive']


def reset():
    clear(send_dir)
    clear(receive_dir)

reset()
