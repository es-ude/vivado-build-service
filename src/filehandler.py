from . import config
from zipfile import ZipFile
import zipfile
import shutil
import os

send_dir = config['Paths']['send']
receive_dir = config['Paths']['receive']
request_file = config['Paths']['request']
bash_script = config['Paths']['bash_script']
test_packet = config['Test']['test_packet']

send_file = os.path.join(send_dir, request_file)


def prepare_request(directories, user):  # Client
    file_list = []

    for directory in directories:
        file_list += get_filepaths(directory)

    task_dir = make_personal_dir(user, send_dir)
    filepath = '/'.join([task_dir, request_file])
    pack(file_list, filepath)

    return serialize(filepath), task_dir


def process_response(data, task_dir):
    result_dir = task_dir + '/result'
    filepath = result_dir + '/result.zip'

    os.mkdir(result_dir)
    deserialize(data, filepath)
    unpack(filepath, result_dir)
    os.remove(filepath)


def process_request(data, user):  # Server
    task_dir = make_personal_dir(user, receive_dir)
    filepath = '/'.join([task_dir, request_file])

    deserialize(data, filepath)
    unpack(filepath, task_dir)
    os.remove(filepath)

    return task_dir


def prepare_response(result_directory):
    files = get_filepaths(result_directory)
    filepath = '/'.join([result_directory, 'result.zip'])
    pack(files, filepath)

    return serialize(filepath)


def make_personal_dir(user, directory):
    client_dirs = os.listdir(directory)
    client_dir = os.path.join(directory, user)

    if user not in client_dirs:
        os.mkdir(client_dir)
        queue_priority = 1
    else:
        user_dir_contents = os.listdir(client_dir)
        if not user_dir_contents:
            queue_priority = 1
        else:
            queue_priority = max([int(_dir) for _dir in user_dir_contents]) + 1

    task_dir = os.path.join(client_dir, str(queue_priority))
    os.mkdir(task_dir)

    return task_dir


def get_filepaths(directory):
    filepaths = []
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            filepaths.append(filepath)
    return filepaths


def serialize(file):
    with open(file, 'rb') as f:
        return f.read()


def deserialize(stream, destination):
    with open(destination, 'wb') as file:
        file.write(stream)


def pack(origin, destination):
    with ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for filepath in origin:
            if test_packet in filepath:
                relative_path = os.path.relpath(filepath, os.path.abspath(test_packet))
            else:
                relative_path = os.path.relpath(filepath, destination)
            archive.write(filepath, relative_path)


def unpack(origin, destination):
    print("\n Files located under '{}'".format(os.path.abspath(destination)))
    with ZipFile(origin, 'r') as archive:
        for file in archive.filelist:
            archive.extract(file, destination)

    print("done unzipping")


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


def reset_test():
    test_dir_client = os.path.join(send_dir, 'test')
    test_dir_server = os.path.join(receive_dir, 'test')

    if os.path.isdir(test_dir_client) and os.path.isdir(test_dir_server):
        clear(test_dir_client)
        clear(test_dir_server)

        os.rmdir(test_dir_client)
        os.rmdir(test_dir_server)


def remove(directory):
    shutil.rmtree(directory)


def create_file(file, directory):
    os.mkdir(directory)
    filepath = os.path.join(directory, file)

    with open(filepath, 'a'):
        pass


def dos2unix(origin, destination):
    with open(destination, "w") as fout:
        with open(origin, "r") as fin:
            for line in fin:
                line = line.replace('\r\n', '\n')
                fout.write(line)
