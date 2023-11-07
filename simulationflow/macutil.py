from docs.config import Config
import re
import uuid

config = Config().get()
delimiter = config['delimiter'].encode()

def find_delimiter_index(stream):
    for i in range(len(stream)):
        if stream[i:i+len(delimiter)] == delimiter:
            return i
        

def get_mac_address_from_stream(stream):
    return stream[:find_delimiter_index(stream)].decode()


def get_mac_address():
    return ('.'.join(re.findall('..', '%012x' % uuid.getnode()))).encode()


def get_data(stream):
    return stream[find_delimiter_index(stream) + len(delimiter):]


def split_stream(stream):
    return [get_mac_address_from_stream(stream), get_data(stream)]