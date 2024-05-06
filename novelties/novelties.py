import os


if __name__ == '__main__':
    db = '/home/julian/chess/database/gameDB/chessDB'
    player = 'Carlsen, M.'
    script = 'findNovelties.tcl'

    os.system(f'tkscid {script} {db} {player}')
