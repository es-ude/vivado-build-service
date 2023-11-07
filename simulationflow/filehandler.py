from zipfile import ZipFile
from docs.config import Config
import os

config = Config().get()

send_dir, receive_dir, filename = config['send'], config['receive'], config['request']
send_file = '/'.join([send_dir, filename])


def prepare_request(directories):  # Client
    file_list = []
    
    try:
        for directory in directories:
            file_list += get_filepaths(directory)

        pack(file_list)

        return serialize(send_file)

    except Exception as e:
        print("An error occurred: {}".format(e))

        return b"Error"


def process_request(data, client_address):  # Server
    try:
        client_dirs = os.listdir(receive_dir)
        client_dir = '/'.join([receive_dir, client_address])

        if not client_address in client_dirs:
            os.mkdir(client_dir)
            queue_priority = 1
        else:        
            queue_priority = max([int(_dir) for _dir in os.listdir(client_dir)]) + 1

        task_dir = '/'.join([client_dir, str(queue_priority)])
        filepath = '/'.join([task_dir, filename])

        os.mkdir(task_dir)
        deserialize(data, filepath)
        unpack(filepath, task_dir)
        os.remove(filepath)

        return task_dir
        
    except Exception as e:
        print("An error occurred: {}".format(e))
        e.with_traceback()


def get_filepaths(directory):
    file_list = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))

    return file_list


def serialize(filepath):
    with open(filepath, 'rb') as file:
        return file.read()


def deserialize(binary, destination):
    with open(destination, 'wb') as file:
        file.write(binary)


def pack(filepaths):
    with ZipFile(send_file, 'w') as archive:
        for filepath in filepaths:
            archive.write(filepath, arcname=filepath.split('\\')[-1])


def unpack(filepath, destination):
    with ZipFile(filepath, 'r') as archive:
        for file in archive.filelist:
            archive.extract(file, destination)
            print("Added '{}'".format(file.filename))
        print('\n')
