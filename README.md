# 🚀 Vivado Simulation Automation Tool

This tool automates Vivado simulations by allowing clients to submit build files to a server over a socket connection, streamlining FPGA development workflows.

---

## 🔧 Client-Side Installation

1. Ensure [`uv`](https://github.com/astral-sh/uv) is installed.
2. Clone this repository:

   ```bash
   git clone https://your-repo-url.git
   cd your-repo-directory
   ```

3. Install dependencies:

   ```bash
   uv install
   ```

---

## 🖥️ Server-Side Installation

Start the build server using:

```bash
python3 -m vbservice.buildserver
```

---

## 🛠️ How to Use the Tool

### 1. Import Required Classes

```python
from vbservice.client import Client
from vbservice.config import ClientConfig, ServerConfig
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
    only_bin_files=True                        # Set to True to download only .bin files
)
```

---

For any issues or contributions, please refer to the [issues](https://github.com/es-ude/vivado-build-service/issues) section of the repository.
