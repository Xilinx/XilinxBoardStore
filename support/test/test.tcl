
if {[catch {
  xhub::get_xstores 
  set_param board.repoPaths [get_property LOCAL_ROOT_DIR [xhub::get_xstores xilinx_board_store]]
  xhub::uninstall [xhub::get_xitems -of_objects [xhub::get_xstores xilinx_board_store]]
  xhub::refresh_catalog [xhub::get_xstores xilinx_board_store]
  xhub::install [xhub::get_xitems -of_objects [xhub::get_xstores xilinx_board_store]]
} result]} {
  puts "Failed to download boards from github."
  puts "error : $result"
} else {
  puts "Successfully downloaded boards from github."
}

if {[catch { 
  set boards_list [get_board_parts]
  foreach board_obj $boards_list {
    set board_interfaces [get_board_part_interfaces -of_objects $board_obj]
    foreach board_interface $board_interfaces {
       get_board_part_pins -of_objects $board_interface 
       get_board_interface_ports -of_objects $board_interface 
    }	
  }

  set boards [get_boards]
  foreach board_obj $boards {
     set board_components [get_board_components -of_objects  $board_obj]
     foreach board_component  $board_components {
       get_board_component_pins -of_objects $board_component  
       get_board_component_modes -of_objects $board_component
       get_board_component_interfaces -of_objects $board_component  	
    }
  }
} result]} {
    puts  "Failed to execute basic board commands on boards  "  
    puts  "error : $result"      
} else {
    puts "Succesfully ran basic board commands on all git boards"
    xhub::uninstall [xhub::get_xitems -of_objects [xhub::get_xstores xilinx_board_store]]
} 

 

