from src.filehandler import prepare_request, process_response, reset
from src import config
from contextlib import closing

import subprocess
import logging
import socket
import select
import sys

logging.getLogger().setLevel(logging.INFO)

chunk_size = config['chunk size']
delimiter = config['delimiter'].encode()
HOST, PORT = config['host'], config['port']

try:
    username = sys.argv[1]
    directories = sys.argv[2:]
except:  # Debug Mode
    reset()
    username = config['debug user']
    directories = ['../build_dir/srcs']

def setup(HOST, PORT, testing=False):
    global directories
    global username

    if testing:
        username = 'testing'
        directories = [config['test packet']]

    request, task_dir = prepare_request(directories, username)
    data = delimiter.join([username.encode(), request]) + delimiter

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

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
        if i != -1: i += 1

    process_response(response, task_dir)

   
def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0


def forward_port(host, port, username, ip):
    if check_socket:
        subprocess.Popen("ssh -Y -L {}:{}:{} {}@{}".format(port, host, port, username, ip), creationflags=subprocess.CREATE_NEW_CONSOLE)


def print_loading_animation(i):
    if i == -1: return    
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
    username = config['username']
    ip = config['ip address']
    forward_port(HOST, PORT, username, ip)
    setup(HOST, PORT)


if __name__ == '__main__':
    main()
