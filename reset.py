from docs.config import Config
import shutil
import os

config = Config().get()
send_dir, receive_dir = config['send'], config['receive']


def reset():
    clear(send_dir)
    clear(receive_dir)


def clear(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:

            if file == 'info.md':
                continue

            os.unlink(os.path.join(root, file))
            print("Removed '{}'".format(file))

        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))
            print("Removed directory '{}'".format(_dir))


reset()
