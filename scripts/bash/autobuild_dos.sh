#!/bin/bash
# $1 Vivado User
# $2 filepath to tcl script 
# $3 task build folder
# $4 result output folder
# $5 filepath to constraints
# $6 only-bin-file: 'output' all-project-files: '*'

# Log file location
LOG_FILE="run.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Clear auto_build folder and log
log_message "Clearing auto_build folder..."
rm -rf /home/"$1"/.autobuild/* 2>> "$LOG_FILE"

# Make directories for Vivado and log each step
log_message "Creating directories for Vivado..."
mkdir -p /home/"$1"/.autobuild/input_srcs/srcs 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/input_srcs/constraints 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/vivado_project 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/output 2>> "$LOG_FILE"
mkdir -p /home/"$1"/.autobuild/tcl_script 2>> "$LOG_FILE"

# Copy constraints into auto_build folder and log
log_message "Copying constraints..."
cp "$5" /home/"$1"/.autobuild/input_srcs/constraints 2>> "$LOG_FILE"

# Copy build folder and log
log_message "Copying build folder..."
cp -r "$3" /home/"$1"/.autobuild/input_srcs/srcs 2>> "$LOG_FILE"

# Let Vivado run and log output (stdout and stderr)
log_message "Running Vivado..."
export XILINXD_LICENSE_FILE=/opt/flexlm/Xilinx.lic
/tools/Xilinx/Vivado/2021.1/bin/vivado -mode tcl -source "$2" >> "$LOG_FILE" 2>&1

# Check if Vivado run was successful
if [ $? -ne 0 ]; then
    log_message "Vivado run failed. Please check the log for errors."
    exit 1
fi

# Copy *bin file to output folder and log
log_message "Copying bin files to output folder..."
cp /home/"$1"/.autobuild/vivado_project/project_1.runs/impl_1/*.bin /home/"$1"/.autobuild/output/ 2>> "$LOG_FILE"

# Copy script in folder and log
log_message "Copying the script to the folder..."
cp /home/"$1"/.autobuild_script/create_project_full_run.tcl /home/"$1"/.autobuild/tcl_script/ 2>> "$LOG_FILE"

# Copy output folder to result folder and log
log_message "Copying output folder to result folder..."
cp -r /home/"$1"/.autobuild/"$6" "$4" 2>> "$LOG_FILE"

# Clear auto_build folder and log
log_message "Clearing auto_build folder..."
rm -rf /home/"$1"/.autobuild/* 2>> "$LOG_FILE"

log_message "Script completed successfully."
