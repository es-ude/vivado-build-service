from simulationflow.filehandler import prepare_request, process_response, reset
from docs.config import Config
import logging
import socket
import select
import sys

logging.getLogger().setLevel(logging.INFO)

config = Config().get()
chunk_size = config['chunk size']
delimiter = config['delimiter'].encode()

try:
    username = sys.argv[1]
    directories = sys.argv[2:]
except:
    reset()
    username = 'dominik'
    directories = ['../Elasic-Ai-Workflow-Demo/ElasticAI-Workflow-Demo/build_20']

request, task_dir = prepare_request(directories, username)

HOST, PORT = config['host'], config['port']
data = delimiter.join([username.encode(), request])

def create_socket():
    logging.info('creating socket')
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    logging.info('connecting')
    ret = s.connect_ex((HOST, PORT)) #BLOCKING

    if ret != 0:
        logging.info('failed to connect!')
        return
    
    logging.info('connected!')
    s.setblocking(False)

    inputs, outputs = [s], [s]
    response = b''

    while inputs:
        logging.info('waiting...')
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.5)

        for s in writable:
            logging.info('sending...')

            s.send(data)            
            # for i in range(0, len(data), chunk_size):
            #     chunk = data[i:i + chunk_size]
            #     sock.sendall(chunk)
            
            logging.info('sent')
            outputs.remove(s)

        for s in readable:
            logging.info(f'reading...')

            chunk = s.recv(chunk_size)
            response += chunk

            logging.info(f'data: {len(response)}')
            logging.info(f'closing...')

            s.close()
            inputs.remove(s)
            break

        for s in exceptional:
            logging.info(f'error')
            inputs.remove(s)
            outputs.remove(s)
            break
    
    process_response(response, task_dir)


def main():
    create_socket()


if __name__ == '__main__':
    main()
