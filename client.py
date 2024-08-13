from src.filehandler import prepare_request, process_response, reset
from src import config
from contextlib import closing

import subprocess
import logging
import socket
import select
import sys

logging.getLogger().setLevel(logging.INFO)

chunk_size = config['Connection']['chunk_size']
delimiter = config['Connection']['delimiter'].encode()
test_packet = [config['Test']['test_packet']]
ip_address = config['SSH']['ip_address']
vnc_user = config['SSH']['username']
#   HOST = config['Connection']['host']
PORT = config['Connection']['port']

username = ''
upload_data_folder = ''
download_folder = ''
only_bin_file = True


def init_system_parameters():
    global username, upload_data_folder, download_folder, only_bin_file

    try:
        username = sys.argv[1]
        upload_data_folder = [sys.argv[2]]
        download_folder = [sys.argv[3]]
        try:
            only_bin_file = bool(sys.argv[4])
        except:
            only_bin_file = False

    except IndexError as e:
        print('You forgot to pass some arguments!\n' +
              'The command should look something like this:\n' +
              '$ python client.py {username} {upload} {download} {only-bin)}\n\n' +
              'Continuing with Sample Data...')

        username = config['Debug']['user']
        upload_data_folder = [config['Debug']['build']]
        download_folder = ''
        only_bin_file = False


def setup(PORT, HOST='localhost', testing=False):
    global username, upload_data_folder, download_folder, only_bin_file

    if testing:
        username = 'test'
        upload_data_folder = test_packet

    request, task_dir = prepare_request(upload_data_folder, username)
    data = delimiter.join([username.encode(), download_folder.encode()] + flags + [request]) + delimiter

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    logging.info('connecting...')
    ret = s.connect_ex((HOST, PORT))

    if ret != 0:
        logging.info('failed to connect!\n')
        return

    logging.info('connected!\n')
    s.setblocking(False)

    i = 0
    inputs, outputs = [s], [s]
    response = b''

    while inputs:
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.5)

        for s in writable:
            logging.info('sending...')
            s.send(data)
            logging.info('sent!\n')
            outputs.remove(s)

        for s in readable:
            chunk = s.recv(chunk_size)
            if not chunk:
                logging.info('\nclosing...\n')
                inputs.remove(s)
                s.close()
                i = -1
                break

            response += chunk

        for s in exceptional:
            logging.info('\nerror')
            inputs.remove(s)
            outputs.remove(s)
            i = -1
            break

        print_loading_animation(i)
        if i != -1:
            i += 1

    process_response(response, task_dir)


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0


def forward_port(host='localhost', port, vnc_user, ip_address):
    if check_socket:
        subprocess.Popen("ssh -Y -L {}:{}:{} {}@{}".format(port, host, port, vnc_user, ip_address),
                         creationflags=subprocess.CREATE_NEW_CONSOLE)


def print_loading_animation(i):
    if i == -1:
        return

    loading = "|/-\\"
    time_in_seconds = i // 2
    sys.stdout.write("\rwaiting... {} (Time: {}:{}{})".format(
        loading[i % len(loading)],
        time_in_seconds // 60,
        "0" if time_in_seconds % 60 < 10 else "",
        time_in_seconds % 60
    ))
    sys.stdout.flush()


def main():
    forward_port(HOST, PORT, vnc_user, ip_address)
    setup(HOST, PORT)


if __name__ == '__main__':
    main()
