import os, sys
import subprocess
import chess
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import evalDB


def searchPositions(pgn: str, script: str, db: str) -> dict:
    """
    Going through each game of a PGN and finding the novelties.
    pgn: str
        Path to the PGN file
    script: str
        Path to the SCID-script which looks if the position is new
    db: str
        Path to the SCID-database to compare the game to
    return -> dict
        A dict indexed by the players with the number of novelties they played.
    """
    novelties = dict()
    # dictionary to count the book moves, values are lists with the number of moves with more than 1000, 100, 10, 1 games
    bookMoves = dict()
    cache = list()
    with open(pgn, 'r') as tournament:
        while (game := chess.pgn.read_game(tournament)):
            white = game.headers["White"]
            black = game.headers["Black"]
            board = game.board()

            for move in game.mainline_moves():
                posBefore = board.fen()
                board.push(move)
                posAfter = board.fen()
                
                if posAfter in cache:
                    break

                search = str(subprocess.run(['tkscid', script, db, posAfter], stdout=subprocess.PIPE).stdout)
                numGames = gamesFromSearchOutput(search)
                if board.turn:
                    player = black
                else:
                    player = white
                if numGames > 1:
                    cache.append(posAfter)
                    if player not in bookMoves.keys():
                        bookMoves[player] = [0, 0, 0, 0]
                    if numGames > 1000:
                        start = 0
                    elif numgames > 100:
                        start = 1
                    elif numgames > 10:
                        start = 2
                    else:
                        start = 3
                    for i in range(start, len(bookMoves[player])):
                        bookMoves[player][i] += 1
                    continue

                if not isMistake(posBefore, posAfter):
                    if player not in novelties.keys():
                        novelties[player] = 1
                    else:
                        novelties[player] += 1
    print(bookMoves)
    return novelties



def gamesFromSearchOutput(output: str) -> int:
    """
    This function takes the output from a SCID search and extracts the number of games
    output: str
        The unformatted output
    return -> int
        The number of games found
    """
    games = re.findall('\d+', output)[0]
    return int(games)


def isMistake(posBefore: str, posAfter: str, mistakeThreshold: int = 70) -> bool:
    """
    This function takes the position before and after a move and determines if the move was a mistake
    posBefore: str
        FEN string of the position before the move
    posAfter: str
        FEN string of the position after the move
    mistakeThreshold: int
        Centipawn loss which counts as a mistake
    return -> bool:
        True if the move was a mistake, False otherwise
    """
    sf = functions.configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    time = 4
    if evalDB.contains(posBefore):
        cpBefore = int(evalDB.getEval(posBefore, False))
    else:
        info = sf.analyse(Board(posBefore), chess.engine.Limit(time=time))
        cpBefore = info['Score']
        # TODO: enter positions into eval DB
    if evalDB.contains(posAfter):
        cpAfter = int(evalDB.getEval(posAfter, False))
    else:
        info = sf.analyse(Board(posAfter), chess.engine.Limit(time=time))
        cpAfter = info['Score']
        # TODO: enter positions into eval DB
    return abs(cpBefore-cpAfter) > mistakeThreshold


if __name__ == '__main__':
    db = '/home/julian/chess/database/gameDB/chessDB'
    player = 'Carlsen, M.'
    script = 'searchPosition.tcl'
    pgn = '../out/test.pgn'
    fen = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'

    o = subprocess.run(['tkscid', script, db, fen], stdout=subprocess.PIPE).stdout
    print(o)
    print(gamesFromSearchOutput(str(o)))
