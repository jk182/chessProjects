import matplotlib.pyplot as plt
import chess
import os, sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions



def depthChange(fen: str, engine: chess.engine, minDepth: int = 1, maxDepth: int = 18) -> list:
    """
    This function evaluates the positions at various depths
    fen: str]
        The position to analyse
    engine: engine
        A configured chess engine
    minDepth: int
        The minimum depth for the analysis
    maxDepth: int
        The maximum depth for the analysis
    return -> list
        A list with all the evaluations
    """
    evals = list()
    board = chess.Board(fen)
    for d in range(minDepth, maxDepth+1):
        info = engine.analyse(board, chess.engine.Limit(depth=d))
        evals.append(info["score"].relative)
    return evals


def isPuzzle(fen: str, engine: chess.engine) -> bool:
    """
    This function looks at the depthChange of a position and determines if the position is a (candidate for a) tactics puzzle
    """
    # To give mates a score
    mateScore = 10000
    evShallow = depthChange(fen, engine, minDepth=1, maxDepth=5)
    evDeep = depthChange(fen, engine, minDepth=18, maxDepth=20)
    startScore = min([s.score(mate_score=mateScore) for s in evShallow])
    endScore = min([s.score(mate_score=mateScore) for s in evDeep])
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


def testLichessPuzzles(dbPath: str, limit: int = None) -> list:
    """
    This function tests which puzzles in the Lichess Puzzle DB are counted as puzzles
    dbPath: str
        Path to the Lichess puzzle database
    limit: int
        The maximum number of puzzles to look at
    return -> list
        List of positions which weren't recognized as puzzles
    """
    failed = list()
    df = pd.read_csv(dbPath)
    if not limit:
        limit = len(df.index)

    
    for i in df.index:
        if i >= limit:
            break
        fen = df['FEN'][i]
        # The puzzle starts with the setup move, so it has to be played before analysing
        move = df['Moves'][i].split(' ')[0]
        board = chess.Board(fen)
        board.push_uci(move)
        fen = board.fen()
        if not isPuzzle(fen, sf):
            failed.append(fen)
            print(fen)
    print(len(failed)/len(list(df['FEN'])))
    return failed


def plotEvalChange(fens: list, engine: chess.engine, minDepth: int = 1, maxDepth: int = 20, filename: str = None):
    """
    This function plots the change in evaluation for various depths in the given FENs
    """
    mateScore = 10000
    colors = ['#689bf2', '#f8a978', '#ff87ca', '#beadfa']
    labels = ['Position 1', 'Position 2', 'Starting Position']
    fig, ax = plt.subplots(figsize=(10,6))
    ax.set_facecolor('#e6f7f2')

    for i, fen in enumerate(fens):
        evals = depthChange(fen, engine, minDepth, maxDepth)
        ax.plot(range(minDepth, maxDepth+1), [s.score(mate_score=mateScore) for s in evals], color=colors[i%len(colors)], label=labels[i%len(labels)])

    ax.set_xlim(minDepth, maxDepth)
    ax.set_ylim(0)
    ax.set_xticks(range(minDepth, maxDepth+1))
    ax.set_xlabel('Depth')
    ax.set_ylabel('Evaluation')
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Evaluation at different Depths')
    # ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()



if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': 1})
    fens = ['r1bq1rk1/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w - - 2 8',
            '8/3RBk2/p3p3/2p2q2/3b4/8/PP4rP/6QK w - - 0 34',
            'b7/5p1k/1b2qp2/1P3N2/3p2P1/7P/2QN4/5K2 b - - 3 33',
            'r2q1r2/p3bkp1/b4n1p/2pn4/3p4/1P3NPB/P1QBPP1P/R3R1K1 w - - 0 20']
    puzzleDB = '~/chess/resources/lichess_db_puzzle-10000.csv'
    # print(findPuzzles('/Users/julian/Desktop/testPGN.pgn', sf))
    # print(testLichessPuzzles(puzzleDB, 2000))
    # print(findPuzzles('../resources/jk_200.pgn', sf))
    # plotEvalChange(['4r2k/pp4pp/7q/3Npr2/2Pn1p2/PP3P2/6PP/1Q1RR2K w - - 6 29', '2rqk2r/1p2ppb1/p2p1Bp1/3b3p/4P3/1B3P2/PPPQ2PP/2KR3R b k - 0 14', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'], sf, filename='../out/evalDepth.png')
    positional = ['2r3k1/1bn3qp/p1p1pr2/1pPpNp2/3P2p1/1P4P1/P2QPPBP/2RR2K1 w - - 0 1']
    plotEvalChange(positional, sf, filename='../out/strategic.png')
    # plotEvalChange(['8/7r/8/5kP1/8/8/5PK1/1R6 w - - 0 57'], sf, maxDepth=30, filename='../out/evalDepth2.png')
    sf.quit()
