# Vivado Simulation Automation Tool

This tool automates Vivado simulations by allowing clients to submit build files to a server over a socket connection, streamlining FPGA development workflows.

---

## 🔧 Client-Side Installation

1. Ensure [`uv`](https://github.com/astral-sh/uv) is installed.
2. Ensure you use python version 3.12 or higher
3. You must be able to connect to the server without entering a password.
The recommended way is to generate an SSH key pair and have an administrator add your public key to the server.
4. Locate your project directory and install the tool using uv:

   ```bash
   uv pip install "git+https://github.com/es-ude/vivado-build-service.git"
   ```

---

## 🖥️ Server-Side Installation

1. Clone and locate the repository:
   ```bash
   git clone https://github.com/es-ude/vivado-build-service
   cd vivado-build-service
   ```
2. Configure the server port inside config/default_server_config.toml and save the config file as server_config.toml

3. Start the build server using:

   ```bash
   python3 -m vbservice.buildserver
   ```

---

## 🛠️ How to Use the Tool

### 1. Import Required Classes

```python
from vbservice import Client
from vbservice import ClientConfig
```

---

### 2. Configure the Client

```python
client_config = ClientConfig(
    server_port=1234,                    # Port where the build server is running
    server_ip_address='192.168.0.1',     # IP address of the build server
    queue_user='your_username',          # Your unique username for the build queue
)
```

---

### 3. Instantiate the Client

```python
client = Client(client_config)
```

---

### 4. Build and Download Project Files

Call the `build()` method to send a synthesis request and retrieve generated files upon success:

```python
client.build(
    upload_dir='path/to/your/vhdl/files',      # Path to your VHDL build files
    download_dir='path/to/save/results',       # Directory to store the generated files
    model_number='fpga_model_123',             # Your specific FPGA model number
    only_bin_files=True                        # Set to True to download only .bin files, logs, and reports
)
```

---

For any issues or contributions, please refer to the [issues](https://github.com/es-ude/vivado-build-service/issues) section of the repository.
