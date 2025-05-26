import os
import shutil
import subprocess
from pathlib import Path

from src.filehandler import get_filepaths, get_report_file_paths, get_filename
from src.report_parser import create_toml_from_vivado_report


def run_vivado_autobuild(tcl_script, build_folder, result_folder, constraints, bin_mode, tcl_args):
    log = get_log(result_folder)
    try:
        clear_autobuild()
        make_directories()
        copy_task_files(constraints, build_folder)
        vivado_command, env = set_vivado_environment(tcl_script, tcl_args)
        run_vivado(vivado_command, env, log)
        copy_autobuild_files(log)
        parse_reports()
        copy_result(result_folder, bin_mode)

    except Exception as e:
        create_log(log, e)
    finally:
        clear_autobuild()


def clear_autobuild():
    shutil.rmtree("~/.autobuild", ignore_errors=True)


def make_directories():
    os.makedirs(f"~/.autobuild/input_srcs/srcs", exist_ok=True)
    os.makedirs(f"~/.autobuild/input_srcs/constraints", exist_ok=True)
    os.makedirs(f"~/.autobuild/vivado_project", exist_ok=True)
    os.makedirs(f"~/.autobuild/bin", exist_ok=True)
    os.makedirs(f"~/.autobuild/tcl_script", exist_ok=True)
    os.makedirs(f"~/.autobuild/reports", exist_ok=True)
    os.makedirs(f"~/.autobuild/toml", exist_ok=True)


def copy_task_files(constraints, build_folder):
    shutil.copy(constraints, f"~/.autobuild/input_srcs/constraints")
    shutil.copytree(build_folder, f"~/.autobuild/input_srcs/srcs", dirs_exist_ok=True)


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


def copy_autobuild_files(log):
    copy_bin_files(log)
    copy_tcl_files()
    copy_report_files()


def copy_bin_files(log):
    bin_source = "~/.autobuild/vivado_project/project_1.runs/impl_1"
    for file in os.listdir(bin_source):
        if file.endswith(".bin"):
            shutil.copy(os.path.join(bin_source, file), "~/.autobuild/bin/")
            break
    else:
        with open(log[1], "w") as f:
            f.write(f"Vivado run failed. Check log: {log[0]}")


def copy_tcl_files():
    shutil.copy("~/.autobuild_script/create_project_full_run.tcl",
                "~/.autobuild/tcl_script/")


def copy_report_files():
    project_dir = "~/.autobuild/vivado_project"
    report_dir = "~/.autobuild/reports"
    reports = get_reports(project_dir)
    for report in reports:
        shutil.copy(report, report_dir)


def get_reports(directory):
    files = get_filepaths(directory)
    reports = get_report_file_paths(files)
    return reports


def parse_reports():
    report_dir = f"~/.autobuild/reports"
    toml_dir = f"~/.autobuild/toml"
    for root, dirs, files in os.walk(report_dir):
        for file in files:
            report_path = Path(root) / file
            toml_filepath = Path(toml_dir) / (get_filename(report_path) + '.toml')
            create_toml_from_vivado_report(report_path, toml_filepath)


def copy_result(result_folder, bin_mode):
    source_path = "~/.autobuild"
    copy_toml(os.path.join(source_path, 'toml'), os.path.join(result_folder, 'toml reports'))
    copy_bin(source_path + bin_mode, result_folder)


def copy_toml(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True)


def copy_bin(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True) if os.path.isdir(
        source) else shutil.copy(
        source, destination)


def create_log(log, e):
    with open(log[1], "w") as f:
        f.write(str(e))
        f.write("\n")
        f.write(f"Vivado run failed. Check log: {log[0]}")


def get_log(result_folder):
    log_file = os.path.join(result_folder, "vivado_run.log")
    err_log = os.path.join(result_folder, "failure.bin")
    return [log_file, err_log]
