def find_delimiter_index(stream, delimiter: bytes):
    for i in range(len(stream)):
        if stream[i:i+len(delimiter)] == delimiter:
            return i
        

def end_reached(stream, delimiter: bytes):
    return stream[-len(delimiter):] == delimiter


def remove_delimiter(data, delimiter: bytes):
    return data[:-len(delimiter)]


def get_left(stream, delimiter: bytes):
    return stream[:find_delimiter_index(stream, delimiter)].decode()


def get_right(stream, delimiter: bytes):
    return stream[find_delimiter_index(stream, delimiter) + len(delimiter):]


def split_stream(stream, delimiter: bytes):
    return [get_left(stream, delimiter), get_right(stream, delimiter)]


def join_streams(streams: list[bytes], delimiter: bytes):
    return delimiter.join(streams) + delimiter
