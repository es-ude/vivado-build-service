import os
import logging
from .user_queue import Task
from .streamutil import split_stream, remove_delimiter
from .filehandler import make_personal_dir_and_get_task, deserialize, unpack


def task_from_raw_request(raw_data: bytes, general_config, receive_folder: str) -> Task:
    client_username, stream = split_stream(raw_data, general_config.delimiter.encode())
    model_number, stream = split_stream(stream, general_config.delimiter.encode())
    only_bin_file, stream = split_stream(stream, general_config.delimiter.encode())
    only_bin_file = bool(int(only_bin_file))

    data = remove_delimiter(stream, general_config.delimiter)

    task = make_personal_dir_and_get_task(
        client_username, receive_folder, model_number, only_bin_file
    )
    filepath = os.path.join(task.path, "build.zip")

    deserialize(data, filepath)
    status = unpack(filepath, task.path)
    logging.info(status)

    os.remove(filepath)
    return task
