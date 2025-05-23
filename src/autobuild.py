import os
import shutil
import subprocess


def run_vivado_autobuild(tcl_script, build_folder, result_folder, constraints, bin_mode, tcl_args):
    log = get_log(result_folder)
    try:
        clear_autobuild()
        make_directories()
        copy_task_files(constraints, build_folder)
        vivado_command, env = set_vivado_environment(tcl_script, tcl_args)
        run_vivado(vivado_command, env, log)
        copy_autobuild_files(result_folder, bin_mode, log)
    except Exception as e:
        create_log(log, e)
    finally:
        clear_autobuild()


def clear_autobuild():
    shutil.rmtree("~/.autobuild", ignore_errors=True)


def make_directories():
    os.makedirs(f"~/input_srcs/srcs", exist_ok=True)
    os.makedirs(f"~/input_srcs/constraints", exist_ok=True)
    os.makedirs(f"~/vivado_project", exist_ok=True)
    os.makedirs(f"~/bin", exist_ok=True)
    os.makedirs(f"~/tcl_script", exist_ok=True)


def copy_task_files(constraints, build_folder):
    shutil.copy(constraints, f"~/input_srcs/constraints")
    shutil.copytree(build_folder, f"~/input_srcs/srcs", dirs_exist_ok=True)


def set_vivado_environment(tcl_script, tcl_args):
    env = os.environ.copy()
    env["XILINXD_LICENSE_FILE"] = "/opt/flexlm/Xilinx.lic"
    vivado_command = [
        "/tools/Xilinx/Vivado/2021.1/bin/vivado", "-mode", "tcl", "-source", tcl_script, "-tclargs", tcl_args
    ]
    return vivado_command, env


def run_vivado(vivado_command, env, log):
    with open(log[0], "w") as log_file:
        subprocess.run(vivado_command, env=env, stdout=log_file, stderr=log_file)


def copy_autobuild_files(result_folder, bin_mode, log):
    bin_source = "~/.autobuild/vivado_project/project_1.runs/impl_1"
    for file in os.listdir(bin_source):
        if file.endswith(".bin"):
            shutil.copy(os.path.join(bin_source, file), "~/.autobuild/bin/")
            break
    else:
        with open(log[1], "w") as f:
            f.write(f"Vivado run failed. Check log: {log[0]}")
    shutil.copy("~/.autobuild_script/create_project_full_run.tcl",
                "~/.autobuild/tcl_script/")
    source_path = "~/.autobuild" + bin_mode
    shutil.copytree(source_path, result_folder, dirs_exist_ok=True) if os.path.isdir(
        source_path) else shutil.copy(
        source_path, result_folder)


def create_log(log, e):
    with open(log[1], "w") as f:
        f.write(str(e))
        f.write("\n")
        f.write(f"Vivado run failed. Check log: {log[0]}")


def get_log(result_folder):
    log_file = os.path.join(result_folder, "vivado_run.log")
    err_log = os.path.join(result_folder, "failure.bin")
    return [log_file, err_log]
