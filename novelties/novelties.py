import os
import subprocess


if __name__ == '__main__':
    db = '/home/julian/chess/database/gameDB/chessDB'
    player = 'Carlsen, M.'
    script = 'searchPosition.tcl'
    pgn = '../out/test.pgn'
    fen = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'

    o = subprocess.run(['tkscid', f'{script}', f'{db}', f'{fen}'], stdout=subprocess.PIPE)
    print(f'Output: {o}')
