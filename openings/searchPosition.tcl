set db [lindex $argv 0]
set fen [lindex $argv 1]
set date [lindex $argv 2]
# the date is the lastest date for the games in the database

sc_base open $db

sc_game new
sc_game startBoard $fen

# searching the date has to be done before the board, as there are no filter options
if {$date ne ""} {
	sc_search header -date "1000.01.01 $date"
}

sc_search board 0 E false false

set n [sc_filter count]
puts $n

sc_base close 1
