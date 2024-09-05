from pathlib import Path
from zipfile import ZipFile
import zipfile
import shutil
import os


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


def pack(base_folder, origin, destination):
    with ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for filepath in origin:
            relative_path = filepath.replace(base_folder,'')
            archive.write(filepath, arcname=relative_path)


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
