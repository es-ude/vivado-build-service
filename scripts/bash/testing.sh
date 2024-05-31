#!/bin/bash
# $1 Vivado User
# $2 filepath to tcl script 
# $3 task build folder
# $4 result output folder
# $5 filepath to constraints

# Create or append to the error log
echo "testing.sh Error Log" > error.log

# Create output directory
mkdir -p "$4"/output >> error.log

# Create completed.bin file
cat > "$4"/output/completed.bin
