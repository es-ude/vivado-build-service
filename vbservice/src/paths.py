from importlib.resources import files
import dataclasses

PACKAGE_ROOT = files("vbservice")

DATA_DIRECTORY = "data"

TCL_SCRIPT = PACKAGE_ROOT.joinpath("scripts/tcl/create_project_full_run.tcl")


@dataclasses.dataclass
class ServerPaths:
    tcl_script: str
    receive_folder: str
