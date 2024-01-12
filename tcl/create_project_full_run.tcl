# run.tcl V1

# NOTE:  typical usage would be "vivado -mode tcl -source run.tcl"



# STEP#1: setup design sources and constraints
create_project project_1 /home/dominik/.autobuild/vivado_project -part xc7s15ftgb196-2 -force
add_files /home/dominik/.autobuild/input_srcs/srcs
add_files -fileset constrs_1 -norecurse /home/dominik/.autobuild/input_srcs/constraints/env5_config.xdc
update_compile_order -fileset sources_1

# STEP#2: run synthesis
launch_runs synth_1  -jobs 6
wait_on_run synth_1
#open_run synth_1 -name netlist_1
#report_timing_summary -delay_type max -report_unconstrained -check_timing_verbose -max_paths 10 -input_pins -file $report_dir/syn_timing.rpt
#report_power -file $report_dir/syn_power.rpt
#report_utilization -file $report_dir/syn_util.rpt


# STEP#2: run synthesis
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 6
wait_on_run impl_1

#open_run impl_1
#report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10 -input_pins -file ./Tutorial_Created_Data/project_bft_batch/imp_timing.rpt
#report_power -file ./Tutorial_Created_Data/project_bft_batch/imp_power.rpt

exit
