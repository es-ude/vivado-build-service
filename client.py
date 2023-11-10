from simulationflow.filehandler import prepare_request
from docs.config import Config
import socket
import sys

config = Config().get()
chunk_size = config['chunk size']
delimiter = config['delimiter'].encode()
username = sys.argv[1]
request = prepare_request(sys.argv[2:], username)

HOST, PORT = config['host'], config['port']
data = delimiter.join([username.encode(), request])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        sock.sendall(chunk)

    sock.close()

# print("Sent:     {}".format(data))
# print("Data sent")
# print("Received: {}".format(received))

""" Example build directory:
../Elasic-Ai-Workflow-Demo/ElasticAI-Workflow-Demo/build_20
00:16:3e:99:0b:db
"""