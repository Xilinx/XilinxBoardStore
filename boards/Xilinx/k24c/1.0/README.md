Validate that the xck24-ubva530-2LV-c is available in your Vivado installation.
Please see details in the board lounge or in user guide UG973: Vivado Release Notes, Installation, and Licensing.

Inorder to install the board files,  copy the ZIP and unzip the contents to desired directory, add below setting in Vivado_init.tcl,  relaunch Vivado 2023.1 and board chooser should show KD* board. 
set_param board.repoPaths <boardfiles_dir>

Go through https://docs.xilinx.com/r/en-US/ug835-vivado-tcl-commands/Tcl-Initialization-Scripts for details on Vivado_init.tcl

For more information on creating the designs using board flow, refer user guide UG994: Using the Platform Board Flow in IP Integrator.

Note: There is a Vivado issue in setting LPDDR4 configuration correctly for the KD240 Starter Kit and K24 C-grade production SOM.  
To work around the issue in Vivado, after instantiating PS and loading board pre-sets , the DDR ECC setting needs to be toggled from disabled -> enabled -> disabled. 
To do that in GUI, copy and paste the 4 commands below to tcl console in Vivado. To workaround in TCL script,  copy and paste following 4 lines at the end of your script, before building the design and it will handle the toggle of ECC settings to apply the workaround:

set_property CONFIG.PSU__DDRC__ECC {Enabled} [get_bd_cells <PS instance name>]
generate_target all [get_files  <filename>.bd]
set_property CONFIG.PSU__DDRC__ECC {Disabled} [get_bd_cells <PS instance name>]
generate_target all [get_files  <filename>.bd]
