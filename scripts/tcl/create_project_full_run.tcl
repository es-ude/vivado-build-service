# run.tcl V3 - exits on any error

# Function to handle errors and exit Vivado
proc exit_on_error {errorMsg} {
    puts "Error: $errorMsg"
    exit 1
}

# Top-level catch block
if {[catch {

    # Check if a custom part number is provided via system arguments
    if {[length $::argv] > 0} {
        set part_number [lindex $::argv 0]
    } else {
        error "No part number provided. Usage: vivado -mode tcl -source run.tcl -part <part_number>"
    }

    # STEP#1: Setup design sources and constraints
    create_project project_1 /home/vivado/.autobuild/vivado_project -part $part_number -force
    add_files /home/vivado/.autobuild/input_srcs/srcs
    add_files -fileset constrs_1 -norecurse /home/vivado/.autobuild/input_srcs/constraints/env5_config.xdc
    update_compile_order -fileset sources_1

    # STEP#2: Run synthesis
    launch_runs synth_1 -jobs 12
    wait_on_run synth_1

    # STEP#3: Run implementation
    set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]
    launch_runs impl_1 -to_step write_bitstream -jobs 12
    wait_on_run impl_1

} errorMsg]} {
    exit_on_error $errorMsg
}

# Exit cleanly if everything succeeds
exit
