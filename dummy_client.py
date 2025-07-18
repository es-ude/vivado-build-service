from vbservice.client import Client
from vbservice.config import ClientConfig

client_config = ClientConfig(
    server_port=2025,
    server_ip_address='65.108.38.237',
    queue_user='dominik',
)

client = Client(client_config)

client.build(
    upload_dir='../build_dir',
    download_dir='tests/download',
    # model_number='TEST FAILURE',
    model_number='xc7s15ftgb196-2',
    only_bin_files=True,
)
