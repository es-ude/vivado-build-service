import dataclasses


@dataclasses.dataclass
class ClientConfig:
    server_port: int
    server_ip_address: str
    queue_user: str


@dataclasses.dataclass
class ServerConfig:
    server_port: int
    num_workers: int = 12


@dataclasses.dataclass
class GeneralConfig:
    chunk_size: int
    delimiter: str
    is_test: bool = False


default_general_config = GeneralConfig(
    chunk_size=1024,
    delimiter='100100010',
)
