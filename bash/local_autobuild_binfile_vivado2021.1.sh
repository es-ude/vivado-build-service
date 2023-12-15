#!/bin/bash
# $1 usr_name
# $2 filepath to tcl script 
# $3 task build folder
# $4 output folder

# Clear auto_build folder
rm -rf /home/$1/.autobuild/*;exit;

# Copy build folder
cp $3 /home/$1/.autobuild/input_srcs

# Let vivado run
export XILINXD_LICENSE_FILE=/opt/flexlm/Xilinx.lic&&/tools/Xilinx/Vivado/2021.1/bin/vivado -mode tcl -source $2;exit;

# Copy *bin file to output folder
mkdir /home/$1/.autobuild/output; cp /home/$1/.autobuild/vivado_project/project_1.runs/impl_1/*.bin /home/$1/.autobuild/output/;exit;

# Copy script in folder
mkdir /home/$1/.autobuild/tcl_script; cp /home/$1/.autobuild_script/create_project_full_run.tcl /home/$1/.autobuild/tcl_script/;exit;

# Copy output folder to download folder
cp /home/$1/.autobuild/output/ $4;exit;

# Make 'completed.txt' infofile
cat > $4/completed.txt;exit;

# Clear auto_build folder
rm -rf /home/$1/.autobuild/*;exit;