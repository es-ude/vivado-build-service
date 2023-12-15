from docs.config import Config

from zipfile import ZipFile
import shutil
import logging
import os

logging.getLogger().setLevel(logging.INFO)

config = Config().get()

send_dir = config['send']
receive_dir = config['receive']
filename = config['request']

send_file = '/'.join([send_dir, filename])

def prepare_request(directories, user):  # Client
    try:
        file_list = []

        for directory in directories:
            file_list += get_filepaths(directory)
        
        task_dir = make_personal_dir(user, send_dir)
        filepath = '/'.join([task_dir, filename])
        pack(file_list, filepath)

        return serialize(filepath), task_dir

    except Exception as e:
        logging.error("An error occurred: {}".format(e))


def process_response(data, task_dir):
    try:
        result_dir = task_dir + '/result'
        filepath = result_dir + '/result.zip'

        os.mkdir(result_dir)
        deserialize(data, filepath)
        unpack(filepath, result_dir)
        os.remove(filepath)

    except Exception as e:
        logging.error("An error occurred: {}".format(e))


def process_request(data, user): # Server
    try:
        task_dir = make_personal_dir(user, receive_dir)
        filepath = '/'.join([task_dir, filename])
        
        deserialize(data, filepath)
        unpack(filepath, task_dir)
        os.remove(filepath)

        return task_dir
        
    except Exception as e:
        logging.error("An error occurred: {}".format(e))


def prepare_response(result_directory):
    try:
        infofile = '/'.join([result_directory, 'completed.txt'])
        os.remove(infofile)

        files = get_filepaths(result_directory)
        filepath = '/'.join([result_directory, 'result.zip'])
        pack(files, filepath)

        return serialize(filepath)

    except Exception as e:
        logging.error("An error occurred: {}".format(e))


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
            logging.info("Sending '{}'".format(filepath.split('\\')[-1]))
        print('\n')


def unpack(origin, destination):
    print(origin)
    with ZipFile(origin, 'r') as archive:
        for file in archive.filelist:
            archive.extract(file, destination)
            logging.info("Added '{}'".format(file.filename))
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


def reset():
    clear(send_dir)
    clear(receive_dir)


def remove(directory):
    shutil.rmtree(directory)


def create_file(filename, directory):
    os.mkdir(directory)
    filepath = '/'.join([directory, filename])
    
    with open(filepath, 'a'):
        pass
         