from importlib.resources import files
import dataclasses

PACKAGE_ROOT = files("vbservice")

TMP_CLIENT_DIR = "tmp/client"
TMP_SERVER_DIR = "tmp/server"

TCL_SCRIPT = PACKAGE_ROOT.joinpath("scripts/tcl/create_project_full_run.tcl")
CONSTRAINTS_FILE = PACKAGE_ROOT.joinpath("scripts/constraints/env5_config.xdc")


@dataclasses.dataclass
class ClientPaths:
    send_dir: str


@dataclasses.dataclass
class ServerPaths:
    tcl_script: str
    constraints: str
    receive_folder: str
