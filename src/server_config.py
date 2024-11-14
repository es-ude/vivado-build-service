import dataclasses


@dataclasses.dataclass
class ServerConfig:
    chunk_size: int
    PORT: int
    tcl_script: str
    constraints: str
    bash_script: str
    test_bash_script: str
    request_file: str
    receive_folder: str
    ssh_username: str
    num_workers: int = 12
    isTest: bool = False
