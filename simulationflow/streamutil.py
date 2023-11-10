from docs.config import Config

config = Config().get()
delimiter = config['delimiter'].encode()

def find_delimiter_index(stream):
    for i in range(len(stream)):
        if stream[i:i+len(delimiter)] == delimiter:
            return i
        

def get_username(stream):
    return stream[:find_delimiter_index(stream)].decode()


def get_data(stream):
    return stream[find_delimiter_index(stream) + len(delimiter):]


def split_stream(stream):
    return [get_username(stream), get_data(stream)]