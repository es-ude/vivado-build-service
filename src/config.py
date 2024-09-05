import dataclasses


@dataclasses.dataclass
class ClientConfig:
    server_vivado_user: str
    server_port: int
    server_ip_address: str
    queue_user: str
    send_dir: str


@dataclasses.dataclass
class ServerConfig:
    server_vivado_user: str
    server_port: int
    tcl_script: str
    constraints: str
    bash_script: str
    receive_folder: str
    num_workers: int = 12


@dataclasses.dataclass
class GeneralConfig:
    chunk_size: int
    delimiter: str
    request_file: str
    is_test: bool = False


default_general_config = GeneralConfig(
    chunk_size=1024,
    delimiter='100100010',
    request_file='build.zip',
)
