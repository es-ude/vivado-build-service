from zipfile import ZipFile
from docs.config import Config
import shutil
import os

config = Config().get()

send_dir, receive_dir, filename = config['send'], config['receive'], config['request']
send_file = '/'.join([send_dir, filename])


def prepare_request(directories, user):  # Client
        file_list = []

    # try:
        for directory in directories:
            file_list += get_filepaths(directory)
        
        task_dir = make_personal_dir(user, send_dir)
        filepath = '/'.join([task_dir, filename])
        pack(file_list, filepath)

        return serialize(filepath)

    # except Exception as e:
    #     print("An error occurred: {}".format(e))


def process_request(data, user):  # Server
    # try:
        task_dir = make_personal_dir(user, receive_dir)
        filepath = '/'.join([task_dir, filename])
        
        deserialize(data, filepath)
        unpack(filepath, task_dir)
        os.remove(filepath)

        return task_dir
        
    # except Exception as e:
    #     print("An error occurred: {}".format(e))


def make_personal_dir(user, directory):
    client_dirs = os.listdir(directory)
    client_dir = '/'.join([directory, user])

    if not user in client_dirs:
        os.mkdir(client_dir)
        queue_priority = 1
    else:        
        queue_priority = max([int(_dir) for _dir in os.listdir(client_dir)]) + 1
    
    task_dir = '/'.join([client_dir, str(queue_priority)]) 
    os.mkdir(task_dir)

    return task_dir


def get_filepaths(directory):
    file_list = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))

    return file_list


def serialize(file):
    with open(file, 'rb') as f:
        return f.read()


def deserialize(stream, destination):
    with open(destination, 'wb') as file:
        file.write(stream)


def pack(origin, destination):
    with ZipFile(destination, 'w') as archive:
        for filepath in origin:
            archive.write(filepath, arcname=filepath.split('\\')[-1])
            print("Sent '{}'".format(filepath.split('\\')[-1]))


def unpack(origin, destination):
    with ZipFile(origin, 'r') as archive:
        for file in archive.filelist:
            archive.extract(file, destination)
            print("Added '{}'".format(file.filename))
        print('\n')


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

def remove(directory):
    shutil.rmtree(directory)

    