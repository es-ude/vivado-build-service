import os
import shutil

bash_dir = 'scripts/bash'
client_dir = 'tmp/client'
server_dir = 'tmp/server'


def dos2unix(origin, destination):
    with open(destination, "w") as f_out:
        with open(origin, "r") as f_in:
            for line in f_in:
                line = line.replace('\r\n', '\n')
                f_out.write(line)


def grant_permissions(f):
    current_permissions = os.stat(f).st_mode
    new_permissions = current_permissions | 0o111
    os.chmod(f, new_permissions)


def delete_contents(directory):
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def configure_bash_scripts():
    for root, dirs, files in os.walk(bash_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if file.split('_')[-1] == 'dos.sh':
                unix_file = os.path.join(bash_dir, "_".join(file.split('_')[:-1])) + '_unix.sh'
                dos2unix(filepath, unix_file)
                grant_permissions(filepath)


def reset_environment():
    delete_contents(client_dir)
    delete_contents(server_dir)


def main():
    configure_bash_scripts()
    reset_environment()


if __name__ == '__main__':
    main()
