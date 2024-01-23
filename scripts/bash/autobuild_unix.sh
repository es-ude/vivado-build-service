#!/bin/bash
# $1 usr_name
# $2 filepath to tcl script 
# $3 task build folder
# $4 result output folder
# $5 filepath to constraints

# Clear auto_build folder
rm -rf /home/"$1"/.autobuild/*

# Make directories for Vivado
mkdir /home/"$1"/.autobuild/input_srcs
mkdir /home/"$1"/.autobuild/input_srcs/srcs
mkdir /home/"$1"/.autobuild/input_srcs/constraints
mkdir /home/"$1"/.autobuild/vivado_project
mkdir /home/"$1"/.autobuild/output
mkdir /home/"$1"/.autobuild/tcl_script

# Copy constraints into auto_build folder
cp "$5" /home/"$1"/.autobuild/input_srcs/constraints

# Copy build folder
cp -r "$3" /home/"$1"/.autobuild/input_srcs/srcs

# Let Vivado run
export XILINXD_LICENSE_FILE=/opt/flexlm/Xilinx.lic
/tools/Xilinx/Vivado/2021.1/bin/vivado -mode tcl -source "$2" >> "$4/run.log" 2>&1

# Copy *bin file to output folder
cp /home/"$1"/.autobuild/vivado_project/project_1.runs/impl_1/*.bin /home/"$1"/.autobuild/output/

# Copy script in folder
cp /home/"$1"/.autobuild_script/create_project_full_run.tcl /home/"$1"/.autobuild/tcl_script/

# Copy output folder to result folder
cp -r /home/"$1"/.autobuild/output/* "$4"

# Clear auto_build folder
rm -rf /home/"$1"/.autobuild/*
