import dataclasses


@dataclasses.dataclass
class ClientConfig:
    queue_user: str
    server_ip_address: str
    server_port: int
    server_vivado_user: str  # For SSH Login
    chunk_size: int
    delimiter: str
    request_file: str
    send_dir: str
    isTest: bool = False
