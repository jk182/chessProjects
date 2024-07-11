import chess
import os, sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def depthChange(fen: str, engine: chess.engine, maxDepth: int = 18) -> list:
    """
    This function evaluates the positions at various depths
    fen: str]
        The position to analyse
    engine: engine
        A configured chess engine
    maxDepth: int
        The maximum depth for the analysis
    return -> list
        A list with all the evaluations
    """
    evals = list()
    board = chess.Board(fen)
    for d in range(1, maxDepth+1):
        info = engine.analyse(board, chess.engine.Limit(depth=d))
        evals.append(info["score"].relative)
    return evals


def isPuzzle(fen: str, engine: chess.engine) -> bool:
    """
    This function looks at the depthChange of a position and determines if the position is a (candidate for a) tactics puzzle
    """
    # To give mates a score
    mateScore = 10000
    evals = depthChange(fen, engine)
    startScore = min([s.score(mate_score=mateScore) for s in evals[:5]])
    endScore = min([s.score(mate_score=mateScore) for s in evals[-3:]])
    return functions.winP(endScore)-functions.winP(startScore) > 20


def findPuzzles(pgnPath: str, engine: chess.engine) -> list:
    """
    This function finds the puzzles in a PGN file.
    return -> list
        List containing the FENs of the puzzle positions.
    """
    puzzles = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                if isPuzzle(board.fen(), engine):
                    print(board.fen())
                    puzzles.append(board.fen())
    return puzzles


if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': 10})
    fens = ['r1bq1rk1/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w - - 2 8',
            '8/3RBk2/p3p3/2p2q2/3b4/8/PP4rP/6QK w - - 0 34',
            'b7/5p1k/1b2qp2/1P3N2/3p2P1/7P/2QN4/5K2 b - - 3 33',
            'r2q1r2/p3bkp1/b4n1p/2pn4/3p4/1P3NPB/P1QBPP1P/R3R1K1 w - - 0 20']
    """
    puzzleDB = '~/chess/resources/lichess_db_puzzle-10000.csv'
    df = pd.read_csv(puzzleDB)
    for i in df.index:
        if i > 15:
            break
        fen = df['FEN'][i]
        move = df['Moves'][i].split(' ')[0]
        # The puzzle starts with the setup move, so it has to be played before analysing
        board = chess.Board(fen)
        board.push_uci(move)
        fen = board.fen()
        print(fen)
        print(isPuzzle(fen, sf))
    """
    print(findPuzzles('../resources/jk_200.pgn', sf))
    sf.quit()
