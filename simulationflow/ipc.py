import zmq

context = zmq.Context()
socket = context.socket(zmq.PUSH)