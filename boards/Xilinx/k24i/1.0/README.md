Validate that the xck24-ubva530-2LVI-i is available in your Vivado installation.
Please see details in the board lounge or in user guide UG973: Vivado Release Notes, Installation, and Licensing.

Inorder to install the board files,  copy the ZIP and unzip the contents to desired directory, add below setting in Vivado_init.tcl,  relaunch Vivado 2023.1 and board chooser should show KD* board. 
set_param board.repoPaths <boardfiles_dir>

Go through https://docs.xilinx.com/r/en-US/ug835-vivado-tcl-commands/Tcl-Initialization-Scripts for details on Vivado_init.tcl

For more information on creating the designs using board flow, refer user guide UG994: Using the Platform Board Flow in IP Integrator.