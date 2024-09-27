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
    analysisTime = 1
    pvs = 3
    wpCutoff = 10
    threats = list()
    POV = not board.turn
    mate_score = 100000

    startEval = sf.analyse(board, chess.engine.Limit(time=analysisTime))['score'].pov(POV).score(mate_score=mate_score)
    board.turn = not board.turn
    threatInfo = sf.analyse(board, chess.engine.Limit(time=analysisTime*1.5), multipv=pvs)
    for info in threatInfo:
        if functions.winP(info['score'].pov(POV).score(mate_score=mate_score)) - wpCutoff >= functions.winP(startEval):
            threats.append(info['pv'][0].uci())
    return threats


if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': '4', 'Hash': '8192'})
    board = chess.Board('rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1')
    print(findThreats(sf, board))
    with open('../resources/bernstein-capablanca.pgn', 'r') as pgn:
        game = chess.pgn.read_game(pgn)
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            threats = findThreats(sf, chess.Board(board.fen()))
            print(move.uci(), threats)
    sf.quit()
