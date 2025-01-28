from client import Client
from src.config import ClientConfig

client_config = ClientConfig(
    server_vivado_user='dominik',
    server_port=2025,
    server_ip_address='65.108.38.237',
    queue_user='dominik',
    send_dir='tmp/client',
)

client = Client(client_config)

client.build(
    upload_dir='../build_dir',
    download_dir='tests/download',
    model_number='xc7s15ftgb196-2',
    only_bin_files=True
)
