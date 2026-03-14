# This script returns how often each move in a given position was played in the database before a given date
# TODO: the tree search doesn't include the date
set db [lindex $argv 0]
set fen [lindex $argv 1]
set endDate [lindex $argv 2]
set startDate [lindex $argv 3]

sc_base open $db

proc ::progressCallBack {args} {
    # This dummy function prevents an error message when calling sc_tree search
}

sc_game new
sc_game startBoard $fen

# searching the date has to be done before the board, as there are no filter options
if {$endDate ne ""} {
	if {$startDate eq ""} {
		set startDate "1000.01.01"
	}
	sc_search header -date "$startDate $endDate"
}

sc_search board 0 E false false

# To include the date filter in the tree search, I need to export all filter games to a PGN and open a new database, where I import all these games
set tempPGN "../out/test.pgn"
set tempDB "../out/openingDB/openingDB"

sc_base export filter PGN $tempPGN
sc_base close 1

set id [sc_base create $tempDB]
sc_base switch $id
sc_base import $id $tempPGN

sc_game new
sc_game startBoard $fen
sc_search board 0 E false false


set searchResult [sc_tree search]
puts $searchResult

# Deleting all temporary files that have been created
exec rm -rf $tempPGN
exec rm -rf ${tempDB}.sg4
exec rm -rf ${tempDB}.si4
exec rm -rf ${tempDB}.sn4
sc_base close $id
