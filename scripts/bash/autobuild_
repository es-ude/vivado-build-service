#!/bin/bash
# $1 Vivado User
# $2 filepath to tcl script 
# $3 task build folder
# $4 result output folder
# $5 filepath to constraints
# $6 only-bin-file: 'output' all-project-files: '*'

# Clear auto_build folder
rm -rf .autobuild/*

# Make directories for Vivado
mkdir .autobuild/input_srcs
mkdir .autobuild/input_srcs/srcs
mkdir .autobuild/input_srcs/constraints
mkdir .autobuild/vivado_project
mkdir .autobuild/output
mkdir .autobuild/tcl_script

# Copy constraints into auto_build folder
cp "$5" .autobuild/input_srcs/constraints

# Copy build folder
cp -r "$3" .autobuild/input_srcs/srcs

# Let Vivado run
export XILINXD_LICENSE_FILE=/opt/flexlm/Xilinx.lic
/tools/Xilinx/Vivado/2021.1/bin/vivado -mode tcl -source "$2" >> "$4/run.log" 2>&1

# Copy *bin file to output folder
cp .autobuild/vivado_project/project_1.runs/impl_1/*.bin .autobuild/output/

# Copy script in folder
cp .autobuild_script/create_project_full_run.tcl .autobuild/tcl_script/

# Copy output folder to result folder
cp -r .autobuild/"$6" "$4"

# Clear auto_build folder
rm -rf .autobuild/*
