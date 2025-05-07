import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import pandas as pd
import statistics


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


def findTrapMoves(board: chess.Board, engine: chess.engine, maxDepth: int, minDepth: int = 5) -> list:
    for move in board.legal_moves:
        newBoard = board.copy()
        newBoard.push(move)
        scores = list()
        for info in engine.analysis(newBoard, limit=chess.engine.Limit(depth=maxDepth)):
            if 'score' not in info.keys():
                continue
            if info["depth"] < minDepth:
                continue
            score = info["score"].relative.score(mate_score=1000)
            scores.append(score)

        print(move)
        print((functions.expectedScore(scores[-1])-functions.expectedScore(min(scores)))/100)


def calculateComplexity(df: pd.DataFrame) -> float:
    """
    This calculates the complexity of the data in a Dataframe
    """
    expScore = [functions.expectedScore(evaluation)/100 for evaluation in list(df["Evaluation"])]
    complexity = statistics.pstdev(expScore)
    return complexity


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
    sf = functions.configureEngine('stockfish', {'Threads': '1', 'Hash': '1'})
    findTrapMoves(chess.Board('1Q5R/5qp1/6kp/8/6P1/1p3P2/1P1r2PK/8 b - - 0 1'), sf, 25)
    sf.quit()
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
