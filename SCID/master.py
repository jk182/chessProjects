import os

database = '/home/julian/chess/database/gameDB/chessDB'
script = 'openingStats.tcl'

os.system(f"tkscid {script} {database}")
