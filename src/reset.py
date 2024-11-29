import os
import shutil


def delete_directories_in(directory):
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def clear(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            os.unlink(os.path.join(root, file))
        for _dir in dirs:
            shutil.rmtree(os.path.join(root, _dir))


def reset_environment():
    delete_directories_in("tmp/client")
    delete_directories_in("tmp/server")
    delete_directories_in("tests/testing-environment/tmp/client")
    delete_directories_in("tests/testing-environment/tmp/server")
    clear("tests/download")


def move_log_and_jou_files(origin, destination):
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), origin))
    log_dir = os.path.join(parent_dir, destination)
    for filename in os.listdir(parent_dir):
        if filename.endswith('.log') or filename.endswith('.jou'):
            file_path = os.path.join(parent_dir, filename)
            destination_path = os.path.join(log_dir, filename)
            shutil.move(file_path, destination_path)


def main():
    reset_environment()
    move_log_and_jou_files(origin=".", destination="log")


if __name__ == '__main__':
    main()
