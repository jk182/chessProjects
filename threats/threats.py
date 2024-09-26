import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions

import chess


def findThreats(sf: chess.engine, board: chess.Board) -> list:
    """
    This function uses Stockfish to find the threats in a position.
    sf: chess.engine
        Configured Stockfish engine
    board: chess.Board
        The current position
    return -> list
        All threat moves as a list.
    """
    winPDifference = 15
    startEval = sf.analyse(board, chess.engine.Limit(time=2))['score'].white().score()
    board.turn = not board.turn
    threatEval = sf.analyse(board, chess.engine.Limit(time=2))['score'].white().score()
    print(startEval, threatEval)


if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': '4', 'Hash': '8192'})
    board = chess.Board('r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQR1K1 b kq - 5 6')
    findThreats(sf, board)
    sf.quit()
