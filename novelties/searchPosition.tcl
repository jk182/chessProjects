set db [lindex $argv 0]
set fen [lindex $argv 1]

sc_base open $db

puts $fen

sc_game new
sc_game startBoard $fen
puts [sc_pos fen]
puts [sc_search board 0 E false false]
# I don't know why this doesn't work
# sc_filter remove 2 1 $gameNR 

sc_base close 1
