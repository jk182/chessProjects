set db [lindex $argv 0]
set player [lindex $argv 1]

set pgn "../out/test.pgn"

# TODO: options to exclude specific games (e.g. no blitz games/titles tuesday

set baseID [sc_base open $db]

# I don't know how to search for the player being white or black
set filter [sc_search header -white $player]
sc_base export filter PGN pgn
set filter [sc_search header -black $player]
sc_base export filter PGN pgn -append true

# sc_base create MEMORY "Player"
# sc_base switch 2
# sc_base import 2 pgn

# puts [sc_tree search]
# sc_game load [sc_filter last]
# sc_base switch 1
# puts [sc_game novelty -older]

sc_base close 1
# sc_base close 2
