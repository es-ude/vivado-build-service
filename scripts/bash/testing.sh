#!/bin/bash
# $1 Vivado User
# $2 filepath to tcl script 
# $3 task build folder
# $4 result output folder
# $5 filepath to constraints

# Function to log errors
log_error() {
    echo "Error: $1" >> error.log
}

# Create or append to the error log
echo "testing.sh Error Log" > error.log

# Create output directory
mkdir -p "$4"/output >> error.log 2>&1 || log_error "Failed to create output directory: $4/output"

# Create completed.bin file
cat > "$4"/output/completed.bin >> error.log 2>&1 || log_error "Failed to create completed.bin file: $4/output/completed.bin"
