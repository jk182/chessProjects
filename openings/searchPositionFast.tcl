set db [lindex $argv 0]

sc_base open $db

set currentDate ""
set startDate "1000.01.01"

while {[gets stdin line] >= 0} {
	lassign [split $line "\t"] fen endDate

	if {$endDate ne $currentDate} {
		# sc_filter reset

		set currendDate $endDate
		sc_search header -date "$startDate $endDate"
	}

	sc_game new
	sc_game startBoard $fen

	sc_search board 0 E false false

	puts [sc_filter count]
	flush stdout
}

sc_base close 1
