# Verify that ZCU670 parts are available in your Vivado installation:
get_parts *xczu67dr* in Viavdo TCL console should return xczu67dr-fsve1156-2-i

# If parts are not available:
Please see details in the board lounge or user guide UG973: Vivado Release Notes, Installation, and Licensing.

# Steps to install board parts : 
1. Copy conetents of this folder to your desired directory 
2. Set below param in Vivado_init.tcl 
set_param board.repo Paths <path_to_board_files_directory> 


#Details on Vivado_init.tcl 
In every launch Vivado looks for a Tcl initialization script in the following locations:

In the software installation: <installdir>/Vivado/version/scripts/Vivado_init.tcl.
(Where <installdir> is the installation directory where the Vivado Design Suite is installed.)
In the local user directory:
a. For Windows : %APPDATA%/Xilinx/Vivado/Vivado_init.tcl
b. For Linux: $HOME/.Xilinx/Vivado/Vivado_init.tcl

#For information on design creation 
Refer user guide UG994: Using the Platform Board Flow in IP Integrator.
