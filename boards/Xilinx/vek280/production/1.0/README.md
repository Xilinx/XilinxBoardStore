Validate that the xcve2802-vsvh1760-2MP-e-S is available in your Vivado installation.
Please see details in the board lounge or in user guide UG973: Vivado Release Notes, Installation, and Licensing.

For more information please refer to user guide UG994: Using the Platform Board Flow in IP Integrator.

Note : As per the schematic, bank 705 & bank 706 are provided with 1.5v (VADJ_FMC), but board file sets these bank pin's I/O standard to support MIPI interface (requires 1.2v).
       User needs to take care of bank 705 & 706 pins I/O standard, if the MIPI interface is added and used in the design through board connections.
