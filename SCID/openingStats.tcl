# TODO: add the option to search starting from a given year
# novelty report

set db [lindex $argv 0]
set player "Caruana"

# -readonly doesn't work
set baseID [sc_base open $db]
puts [sc_base current]

# this is supposed to set it to readonly, it doesn't work
sc_base isReadOnly $baseID set
puts [sc_base isReadOnly $baseID]

# ecoStats isn't recognized
# puts [sc_base ecoStats $baseID]

puts [sc_base numGames $baseID]
# sc_base stats baseId <dates|eco ?|flag ?|flags|ratings|results>
# for eco and flag one adds the string they want, i.e. 'eco "B90"'
# Output: TotalGames WhiteWins Draws BlackWins NoResult(I guess) Score
puts [sc_base stats $baseID eco "B90"]

# This throws some random internal error
# sc_filter reset $baseID

# this doesn' return anything, it only changes the filter; -eco is another option
set filter [sc_search header -white $player]
puts [sc_filter stats]
# this leads to a Segmentation fault
# puts [sc_filter stats year 2021]

# Not sure if there is a better way to do it, I export the current filter as a PGN, 
# create a new database in memory, load the PGN and then I can run the stats
sc_base export filter PGN "test.pgn"
sc_base create MEMORY "Test"
sc_base switch 2
sc_base import 2 "test.pgn"
puts [sc_tree search]

# Loading and printing a game
# set game [sc_game load 1717]
# puts [sc_game pgn]

# this leads to a Segmentation fault 
# puts [sc_game novelty -older]

# sc_eco read
# puts [sc_eco summary "B" 1]

# puts [sc_filter last $baseID] 

puts "Done"
