import os
import shutil
import subprocess


def run_vivado_autobuild(vivado_user, tcl_script, build_folder, result_folder, constraints, bin_mode, tcl_args):
    print("##Running vivado autobuild...")

    autobuild_path = f"/home/{vivado_user}/.autobuild"
    log_file = os.path.join(autobuild_path, "vivado_run.log")

    shutil.rmtree(autobuild_path, ignore_errors=True)

    os.makedirs(f"{autobuild_path}/input_srcs/srcs", exist_ok=True)
    os.makedirs(f"{autobuild_path}/input_srcs/constraints", exist_ok=True)
    os.makedirs(f"{autobuild_path}/vivado_project", exist_ok=True)
    os.makedirs(f"{autobuild_path}/bin", exist_ok=True)
    os.makedirs(f"{autobuild_path}/tcl_script", exist_ok=True)

    shutil.copy(constraints, f"{autobuild_path}/input_srcs/constraints")
    shutil.copytree(build_folder, f"{autobuild_path}/input_srcs/srcs", dirs_exist_ok=True)

    env = os.environ.copy()
    env["XILINXD_LICENSE_FILE"] = "/opt/flexlm/Xilinx.lic"
    vivado_command = [
        "/tools/Xilinx/Vivado/2021.1/bin/vivado", "-mode", "tcl", "-source", tcl_script, "-tclargs", tcl_args
    ]

    with open(log_file, "w") as log:
        process = subprocess.run(vivado_command, env=env, stdout=log, stderr=log)
    if process.returncode != 0:
        raise RuntimeError(f"Vivado run failed. Check log: {log_file}")

    bin_source = f"{autobuild_path}/vivado_project/project_1.runs/impl_1"
    for file in os.listdir(bin_source):
        if file.endswith(".bin"):
            shutil.copy(os.path.join(bin_source, file), f"{autobuild_path}/bin/")

    shutil.copy(f"/home/{vivado_user}/.autobuild_script/create_project_full_run.tcl", f"{autobuild_path}/tcl_script/")

    source_path = f"{autobuild_path}/{bin_mode}"
    shutil.copytree(source_path, result_folder, dirs_exist_ok=True) if os.path.isdir(source_path) else shutil.copy(
        source_path, result_folder)

    shutil.rmtree(autobuild_path, ignore_errors=True)
