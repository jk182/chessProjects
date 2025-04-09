import chess
from chess import pgn
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from functions import configureEngine
import pickle


def getEqualEndgameScore(pgnPath: str, cachePath: str = None):
    totalGames = 0
    blitzGames = 0
    rapidGames = 0
    chess960Games = 0
    endings = 0
    cache = dict()

    """
    if cachePath:
        with open(cachePath, 'rb') as pick:
            cache = pickle.load(pick)
    """


    stockfish = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            totalGames += 1
            event = game.headers['Event']
            if 'blitz' in event.lower():
                blitzGames += 1
            elif 'rapid' in event.lower():
                rapidGames += 1
            elif 'freestlye' in event.lower() or 'fischer random' in event.lower():
                chess960Games += 1
            else:
                board = chess.Board()
                for move in game.mainline_moves():
                    board.push(move)
                    if isEndgame(board):
                        fen = board.fen()
                        if fen in cache.keys():
                            score = cache[fen]
                        else:
                            info = stockfish.analyse(board, chess.engine.Limit(time=5))
                            score = info['score'].white().score()
                            print(score)
                            cache[fen] = score
                        if abs(score) < 500:
                            print('Equal ending')
                        endings += 1
                        break

    print(cache)
    if cachePath:
        with open(cachePath, 'wb') as pick:
            pickle.dump(cache, pick) 
    print(totalGames)
    print(blitzGames)
    print(rapidGames)
    print(chess960Games)
    print(endings)
    stockfish.quit()


def isEndgame(position: chess.Board) -> bool:
    """
    This function determins if a position is an endgame
    """
    pieces = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
    pieceCount = 0
    for piece in pieces:
        for color in [chess.WHITE, chess.BLACK]:
            pieceCount += len(list(position.pieces(piece, color)))
    return pieceCount <= 6


if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    getEqualEndgameScore(carlsenGames, cachePath='../resources/carslenEndingsCache.pickle')
