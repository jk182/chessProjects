# Future Idea: calculate how much a player narrows the known moves
import os, sys
import subprocess
import chess
import re
import pickle

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import evalDB


def searchPositions(pgn: str, script: str, db: str) -> tuple:
    """
    Going through each game of a PGN and finding the novelties.
    pgn: str
        Path to the PGN file
    script: str
        Path to the SCID-script which looks if the position is new
    db: str
        Path to the SCID-database to compare the game to
    return -> tuple
        Tuple containing dictionaries with the novelties and book moves
    """
    novelties = dict()
    # dictionary to count the book moves, values are lists with the number of moves with more than 10000, 1000, 100, 10, 1 games
    bookMoves = dict()
    cache = dict()
    gameNR = 1
    with open(pgn, 'r') as tournament:
        while (game := chess.pgn.read_game(tournament)):
            print(f'Starting with game {gameNR}')
            gameNR += 1

            white = game.headers["White"]
            black = game.headers["Black"]
            board = game.board()

            print(white, black)

            for move in game.mainline_moves():
                posBefore = board.fen()
                board.push(move)
                posAfter = board.fen()
                
                if posAfter in cache.keys():
                    numGames = cache[posAfter]
                else:
                    search = str(subprocess.run(['tkscid', script, db, posAfter], stdout=subprocess.PIPE).stdout)
                    numGames = gamesFromSearchOutput(search)
                    cache[posAfter] = numGames

                if board.turn:
                    player = black
                else:
                    player = white
                if numGames > 1:
                    if player not in bookMoves.keys():
                        bookMoves[player] = [0, 0, 0, 0, 0]
                    if numGames > 10000:
                        start = 0
                    elif numGames > 1000:
                        start = 1
                    elif numGames > 100:
                        start = 2
                    elif numGames > 10:
                        start = 3
                    else:
                        start = 4
                    for i in range(start, len(bookMoves[player])):
                        bookMoves[player][i] += 1
                    continue

                if not isMistake(posBefore, posAfter):
                    if player not in novelties.keys():
                        novelties[player] = 1
                    else:
                        novelties[player] += 1
                    print(f'Novelty: {move}')
                break
    return (novelties, bookMoves)



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
    time = 3
    # if evalDB.contains(posBefore):
    if False:
        cpBefore = int(evalDB.getEval(posBefore, False))
    else:
        info = sf.analyse(chess.Board(posBefore), chess.engine.Limit(time=time))
        cpBefore = info['score'].white().score()
        # TODO: enter positions into eval DB
    # if evalDB.contains(posAfter):
    if False:
        cpAfter = int(evalDB.getEval(posAfter, False))
    else:
        info = sf.analyse(chess.Board(posAfter), chess.engine.Limit(time=time))
        cpAfter = info['score'].white().score()
        # TODO: enter positions into eval DB
    sf.quit()
    return abs(cpBefore-cpAfter) > mistakeThreshold


if __name__ == '__main__':
    db = '/home/julian/chess/database/gameDB/novelties'
    player = 'Carlsen, M.'
    script = 'searchPosition.tcl'
    pgn = '../out/candidates2024-WDL+CP.pgn'
    fen = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'

    o = subprocess.run(['tkscid', script, db, fen], stdout=subprocess.PIPE).stdout
    print(o)
    print(gamesFromSearchOutput(str(o)))
    nov, book = searchPositions(pgn, script, db)
    print(nov, book)
    with open(f'../out/candidates-novelties.pkl', 'wb+') as f:
        pickle.dump(nov, f)
    with open(f'../out/candidates-bookMoves.pkl', 'wb+') as f:
        pickle.dump(book, f)
