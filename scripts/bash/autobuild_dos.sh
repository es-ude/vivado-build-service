#!/bin/bash
# $1 Vivado User
# $2 filepath to tcl script 
# $3 task build folder
# $4 result output folder
# $5 filepath to constraints
# $6 only bin file => 'bin'
#    all project files => '*'
# $7 tcl arguments

LOG_FILE="run.log"

log_message() {
    echo "$(date '+%d.%m.%Y %H:%M') - $1" > "$LOG_FILE"
}

log_message "Clearing auto_build folder..."
rm -rf /home/"$1"/.autobuild/* 2>> "$LOG_FILE"

log_message "Creating directories for Vivado..."
mkdir -p /home/"$1"/.autobuild/input_srcs/srcs 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/input_srcs/constraints 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/vivado_project 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/output 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/tcl_script 2>> "$LOG_FILE"

log_message "Copying constraints..."
cp "$5" /home/"$1"/.autobuild/input_srcs/constraints 2>> "$LOG_FILE"

log_message "Copying build folder..."
cp -r "$3" /home/"$1"/.autobuild/input_srcs/srcs 2>> "$LOG_FILE"

log_message "Running Vivado..."
export XILINXD_LICENSE_FILE=/opt/flexlm/Xilinx.lic
/tools/Xilinx/Vivado/2021.1/bin/vivado -mode tcl -source "$2" -tclargs "$7" >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    log_message "Vivado run failed. Please check the log for errors."
    exit 1
fi

log_message "Copying bin files to bin folder..."
cp /home/"$1"/.autobuild/vivado_project/project_1.runs/impl_1/*.bin /home/"$1"/.autobuild/bin/ 2>> "$LOG_FILE"

log_message "Copying the script to the folder..."
cp /home/"$1"/.autobuild_script/create_project_full_run.tcl /home/"$1"/.autobuild/tcl_script/ 2>> "$LOG_FILE"

log_message "Copying bin folder or bin files to result folder..."
# shellcheck disable=SC2086
cp -r /home/"$1"/.autobuild/$6 "$4" 2>> "$LOG_FILE"

log_message "Clearing auto_build folder..."
rm -rf /home/"$1"/.autobuild/* 2>> "$LOG_FILE"

log_message "Script completed successfully."
