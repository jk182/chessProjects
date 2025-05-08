import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import pandas as pd
import statistics
import matplotlib.pyplot as plt


def getEngineAnalysis(board: chess.Board, engine: chess.engine, maxDepth: int) -> pd.DataFrame:
    """
    This analyses the position up to the maximum depth and returns information for all depths in a dataframe
    """
    data = dict()
    columns = ["FEN", "Depth", "Nodes", "NPS", "Move", "Evaluation"]
    for c in columns:
        data[c] = list()
    # Do I need to clear the hash?
    info = engine.analysis(board, limit=chess.engine.Limit(depth=maxDepth))
    for i in info:
        if 'string' in i.keys():
            continue
        data["FEN"].append(board.fen())
        data["Depth"].append(i["depth"])
        data["Nodes"].append(i["nodes"])
        data["NPS"].append(i["nps"])
        data["Move"].append(i["pv"][0].uci())
        data["Evaluation"].append(i["score"].white().score(mate_score=10000))
    df = pd.DataFrame(data)
    return df


def findTrapMoves(board: chess.Board, engineOptions: tuple, maxDepth: int, minDepth: int = 5, referenceDepth: int = 25) -> list:
    trapErrors = list()
    for move in board.legal_moves:
        newBoard = board.copy()
        newBoard.push(move)
        scores = list()
        engine = functions.configureEngine(*engineOptions)
        for info in engine.analysis(newBoard, limit=chess.engine.Limit(depth=maxDepth)):
            if 'score' not in info.keys():
                continue
            if info["depth"] < minDepth:
                continue
            score = info["score"].relative.score(mate_score=1000)
            scores.append(score)
        engine.quit()
        drop = (functions.expectedScore(scores[-1])-functions.expectedScore(min(scores)))
        if drop >= 10:
            trapErrors.append((str(move), drop/100))
    return trapErrors


def calculateComplexity(df: pd.DataFrame) -> float:
    """
    This calculates the complexity of the data in a Dataframe
    """
    expScore = [functions.expectedScore(evaluation)/100 for evaluation in list(df["Evaluation"])]
    complexity = statistics.pstdev(expScore)
    return complexity


def plotExpectedScoreChangeByDepth(posMoves: list, engineOptions: tuple, maxDepth: int, minDepth: int = 1, filename: str = None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')

    colors = ['#6096B4', '#7ed3b2', '#FF87CA', '#BEADFA', '#F8A978', '#E97777', '#435560'] 

    for i, (pos, move) in enumerate(posMoves):
        board = chess.Board(pos)
        board.push(chess.Move.from_uci(move))
        engine = functions.configureEngine(*engineOptions)
        evaluations = list()
        
        for info in engine.analysis(board, limit=chess.engine.Limit(depth=maxDepth)):
            if 'score' not in info.keys():
                continue
            if info["depth"] < minDepth:
                continue
            score = info["score"].pov(not board.turn).score(mate_score=1000)
            evaluations.append(score)

        print(evaluations)
        plt.plot(range(minDepth, maxDepth+1), [functions.expectedScore(score) for score in evaluations], color=colors[i], label=move)
        engine.quit()
        
    ax.legend()
    ax.set_xlim(minDepth, maxDepth)

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


if __name__ == '__main__':
    """
    openings = {'Starting position': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 
            '1.e4': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1',
            'Berlin': 'r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
            'Morphy Defence': 'r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4',
            'Marshall Gambit': 'r1bq1rk1/2p1bppp/p1n2n2/1p1pp3/4P3/1BP2N2/PP1P1PPP/RNBQR1K1 w - - 0 9',
            'Open Sicilian': 'rnbqkbnr/pp2pppp/3p4/8/3pP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 4',
            "King's Gambit": 'rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2'}
    """
    testPositions = {'Botvinnik after dxc4': 'rnbqkb1r/pp3ppp/2p1pn2/6B1/2pP4/2N2N2/PP2PPPP/R2QKB1R w KQkq - 0 6',
                     'Botvinnik after e4': 'rnbqkb1r/pp3ppp/2p1pn2/6B1/2pPP3/2N2N2/PP3PPP/R2QKB1R b KQkq - 0 6',
                     'Botvinnik after Bxg5': 'rnbqkb1r/p4p2/2p1pn2/1p2P1B1/2pP4/2N5/PP3PPP/R2QKB1R b KQkq - 0 10'}
    traps = {'Before': '5r2/1p1r1k2/p2Pbpp1/2p1np2/4pN2/1P5P/P1PRBPP1/2K4R w - - 0 1',
             'After': '5r2/1p1r1k2/p2Pbpp1/2p1np2/4pN2/1P5P/P1PRBPP1/2K1R3 b - - 1 1',
             '2': '1Q5R/5qp1/6kp/8/6P1/1p3P2/1P1r2PK/8 b - - 0 1'}
    openingTraps = {'Sicilian': 'rnbqkb1r/pp2pppp/3p1n2/2p5/4P3/2P2N2/PP1PBPPP/RNBQK2R b KQkq - 2 4',
                    'Englund': 'rnbqk2r/ppp1nppp/3P4/2b5/8/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 5',
                    'Lasker Trap': 'rnbqk1nr/ppp2ppp/8/4P3/1bP5/4p3/PP1B1PPP/RN1QKBNR w KQkq - 0 6',
                    'Blackburne Shilling Gambit': 'r1bqkbnr/pppp1ppp/8/4p3/2BnP3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4'}
    sfConfig = ('stockfish', {'Threads': '1', 'Hash': '1'})
    posMoves = [('rnbqkb1r/pp2pppp/3p1n2/2p5/4P3/2P2N2/PP1PBPPP/RNBQK2R b KQkq - 2 4', 'f6e4')]
    plotExpectedScoreChangeByDepth(posMoves, sfConfig, 25)
    """
    for name, fen in openingTraps.items():
        print(name, findTrapMoves(chess.Board(fen), sfConfig, 23))
    """
    """
    for name, fen in traps.items():
        sf = functions.configureEngine('stockfish', {'Threads': '1', 'Hash': '1'})
        board = chess.Board(fen)
        df = getEngineAnalysis(board, sf, 25)
        comp = calculateComplexity(df)
        print(name, comp)
        print(df)
        sf.quit()
    """
