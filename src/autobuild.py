import os
import shutil
import subprocess


def run_vivado_autobuild(tcl_script, build_folder, result_folder, constraints, bin_mode, tcl_args):
    print("##Running vivado autobuild...")

    log_file = os.path.join(result_folder, "vivado_run.log")

    shutil.rmtree("~/.autobuild", ignore_errors=True)

    os.makedirs(f"~/input_srcs/srcs", exist_ok=True)
    os.makedirs(f"~/input_srcs/constraints", exist_ok=True)
    os.makedirs(f"~/vivado_project", exist_ok=True)
    os.makedirs(f"~/bin", exist_ok=True)
    os.makedirs(f"~/tcl_script", exist_ok=True)

    shutil.copy(constraints, f"~/input_srcs/constraints")
    shutil.copytree(build_folder, f"~/input_srcs/srcs", dirs_exist_ok=True)

    env = os.environ.copy()
    env["XILINXD_LICENSE_FILE"] = "/opt/flexlm/Xilinx.lic"
    vivado_command = [
        "/tools/Xilinx/Vivado/2021.1/bin/vivado", "-mode", "tcl", "-source", tcl_script, "-tclargs", tcl_args
    ]
    err_log = os.path.join(result_folder, "failure.bin")
    try:
        with open(log_file, "w") as log:
            subprocess.run(vivado_command, env=env, stdout=log, stderr=log)
        bin_source = "~/.autobuild/vivado_project/project_1.runs/impl_1"
        for file in os.listdir(bin_source):
            if file.endswith(".bin"):
                shutil.copy(os.path.join(bin_source, file), "~/.autobuild/bin/")
                break
        else:
            with open(err_log, "w") as f:
                f.write(f"Vivado run failed. Check log: {log_file}")
        shutil.copy("~/.autobuild_script/create_project_full_run.tcl",
                    "~/.autobuild/tcl_script/")
        source_path = "~/.autobuild" + bin_mode
        shutil.copytree(source_path, result_folder, dirs_exist_ok=True) if os.path.isdir(
            source_path) else shutil.copy(
            source_path, result_folder)
    except Exception as e:
        with open(err_log, "w") as f:
            f.write(str(e))
            f.write("\n")
            f.write(f"Vivado run failed. Check log: {log_file}")
    finally:
        shutil.rmtree("~/.autobuild", ignore_errors=True)
