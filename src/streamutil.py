

def find_delimiter_index(stream, delimiter):
    for i in range(len(stream)):
        if stream[i:i+len(delimiter)] == delimiter:
            return i
        

def end_reached(stream, delimiter):
    return stream[-len(delimiter):] == delimiter


def remove_delimiter(data, delimiter):
    return data[:-len(delimiter)]


def get_username(stream, delimiter):
    return stream[:find_delimiter_index(stream,delimiter)].decode()


def get_data(stream, delimiter):
    return stream[find_delimiter_index(stream, delimiter) + len(delimiter):]


def split_stream(stream, delimiter):
    return [get_username(stream, delimiter), get_data(stream, delimiter)]
