import chess
import os, sys
import math
import scipy.integrate as integrate
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import pandas as pd
import polars as pl
import statistics
import matplotlib.pyplot as plt
import pickle
import time


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


def analyseLegalMoves(board: chess.Board, engine: chess.engine, maxDepth: int) -> dict:
    moves = dict()
    for move in board.legal_moves:
        moves[move.uci()] = list()
        for depth in range(1, maxDepth+1):
            info = engine.analyse(board, limit=chess.engine.Limit(depth=depth), root_moves=[move])
            if board.turn:
                moves[move.uci()].append(info["score"].white().score(mate_score=1000))
            else:
                moves[move.uci()].append(info["score"].black().score(mate_score=1000))
        
    return dict(reversed(sorted(moves.items(), key=lambda x: x[1][-1])))


def mu(x: int, y: int) -> float:
    if x == 0 and y == 0:
        return 0
    return (x-y) / (x**2 + y**2)


def absDiff(diffFunction, X: list) -> float:
    val = 0
    for i in range(len(X)):
        for j in range(len(X)):
            val += diffFunction(X[i], X[j])**2
    return val**(1/2)


def tau(muFunction, X: list, Y: list, muX: float = None, muY: float = None) -> float:
    val = 0
    for i in range(len(X)):
        for j in range(len(Y)):
            val += muFunction(X[i], X[j]) * muFunction(Y[i], Y[j])

    if muX is None:
        muX = absDiff(muFunction, X)
    if muY is None:
        muY = absDiff(muFunction, Y)

    if muX == 0 or muY == 0:
        return 0

    val /= (muX * muY)
    return val


def complexityBR(L: list, depth: int, muFunction=mu, tauFunction=tau) -> float:
    """
    This is an implementation of the complexity function in the paper 'Quantifying Depth and Complexity of Thinking and Knowledge' by Biswas and Regan
    """
    comp = 1

    for d in range(1, depth):
        ld = [v[d-1] for v in L]
        ld1 = [v[d] for v in L]
        comp -= 1/(depth-1) * tauFunction(muFunction, ld, ld1)

    return comp


def delta(L: list, i: int, d: int, a: float = 1) -> float:
    vMax = max([L[j][d-1] for j in range(len(L))])
    v = L[i][d-1]

    if vMax < 0 and v < 0:
        return math.log(abs(v)+1) - math.log(abs(vMax)+1)
    if v < 0:
        return math.log(abs(v)+1) + math.log(abs(vMax)+1)

    return math.log(vMax+1) - math.log(v+1)


def vFunction(a: float, b: float, c: float = 1) -> float:
    if a == 0 and b == 0:
        return 1
    return math.exp((-2 * a * b) / (c * (a + b)))


def dampenedSwing(L: list, d: int, e: int) -> float:
    swing = 0
    for i in range(len(L)):
        deltaID = delta(L, i, d)
        deltaIE = delta(L, i, e)
        swing += vFunction(deltaID, deltaIE) * abs(deltaID - deltaIE)
    return swing


def aggregateSwing(L: list, maxDepth: int) -> float:
    swing = 0
    for d in range(1, maxDepth):
        swing += dampenedSwing(L, d, maxDepth)

    return swing


def weightedSwing(L: list, weights: list, maxDepth: int) -> float:
    swing = 0
    for d in range(1, maxDepth):
        swing += weights[d-1] * dampenedSwing(L, d, d+1)

    return swing


def weightedSwingList(L: list, weights: list, maxDepth: int) -> list:
    """
    This function returns the weighted swings as a list, to only call this function once
    """
    return [weights[d-1] * dampenedSwing(L, d, d+1) for d in range(1, maxDepth)]


def psi(L: list, e: int, weights: list, maxDepth: int) -> float:
    return (weightedSwing(L, weights, e+1) -  (1/2) * weightedSwing(L, weights, maxDepth)) / (weights[e-2] * dampenedSwing(L, e-1, e))


def psiWSL(L: list, wSwingList: list, e: int, weights: list) -> float:
    """
    Implementation of the psi function with the weighted swing list
    """
    return (sum(wSwingList[:e]) - 1/2 * sum(wSwingList)) / (weights[e-1] * dampenedSwing(L, e, e+1)) # different indices in the denominator than the paper, but this should be correct


def roh(L: list, weights: list, maxDepth: int) -> float:
    wSwingList = weightedSwingList(L, weights, maxDepth)
    # this calculates the minimum (which should be correct), not the maximum as stated in the paper
    for e in range(1, maxDepth):
        if sum(wSwingList[:e]) >= 1/2 * sum(wSwingList):
            finalE = e
            break

    return finalE - psiWSL(L, wSwingList, finalE, weights)


def difficultyBR(board: chess.Board, engine: chess.engine, maxDepth: int):
    L = list(analyseLegalMoves(board, engine, maxDepth).values())
    weights = [depth/sum([d for d in range(1, maxDepth)]) for depth in range(1, maxDepth)]

    return complexityBR(L, maxDepth) * roh(L, weights, maxDepth)


async def analyseLegalMovesAsync(board: chess.Board, maxDepth: int) -> dict:
    # engine = functions.configureEngine(*engineConfig)
    transport, engine = await chess.engine.popen_uci('stockfish')
    await engine.configure({"Threads": 1, "Hash": 1})
    moves = dict()
    for move in board.legal_moves:
        moves[move.uci()] = list()
        for depth in range(1, maxDepth+1):
            info = await engine.analyse(board, limit=chess.engine.Limit(depth=depth), root_moves=[move])
            if board.turn:
                moves[move.uci()].append(info["score"].white().score(mate_score=1000))
            else:
                moves[move.uci()].append(info["score"].black().score(mate_score=1000))
        
    await engine.quit()

    return dict(reversed(sorted(moves.items(), key=lambda x: x[1][-1])))


async def analysisWorker(workerID: int, queue: asyncio.Queue, results: dict, maxDepth: int):
    while True:
        item = await queue.get()
        print(queue.qsize())

        try:
            if item is None:
                return

            posID, fen = item
            result = await analyseLegalMovesAsync(chess.Board(fen), maxDepth)
            results[posID] = result

        finally:
            queue.task_done()


async def runMultipleThreads(fens: list, depth: int, nThreads: int) -> list:
    queue = asyncio.Queue()
    results = dict()

    for posID, fen in enumerate(fens):
        queue.put_nowait((posID, fen))

    workers = [asyncio.create_task(analysisWorker(workerID, queue, results, depth)) for workerID in range(nThreads)]

    await queue.join()
    for _ in range(nThreads):
        queue.put_nowait(None)

    await asyncio.gather(*workers)
    return [result for result in sorted(results.items())]


def getTestData(pgnPath: str, engineConfig: dict, maxDepth: int, threads: int = 6) -> pl.DataFrame:
    data = dict()
    keys = ['White', 'Black', 'WhiteElo', 'BlackElo', 'FEN', 'MovePlayed']
    for key in keys:
        data[key] = list()

    moveNumbers = [20, 25, 30]
    fens = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            board = game.board()

            for move in game.mainline_moves():
                if board.fullmove_number in moveNumbers:
                    fens.append(board.fen())
                    
                    moveData = [game.headers["White"],
                            game.headers["Black"],
                            game.headers["WhiteElo"],
                            game.headers["BlackElo"],
                            board.fen(),
                            move.uci()]

                    for i, key in enumerate(keys):
                        data[key].append(moveData[i])

                board.push(move)

    fens = data['FEN']
    moveEvaluations = asyncio.run(runMultipleThreads(fens, maxDepth, threads))

    data['Moves'] = [list(moves[1].keys()) for moves in sorted(moveEvaluations)]
    data['Evaluations'] = [list(moves[1].values()) for moves in sorted(moveEvaluations)]

    return pl.DataFrame(data)


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

    colors = ['#fa5a5a', '#49d676', '#689bf2', '#F8A978', '#6096B4', '#FF87CA', '#7ed3b2', '#BEADFA', '#E97777', '#435560'] 

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

        plt.plot(range(minDepth, maxDepth+1), [functions.expectedScore(score)/100 for score in evaluations], color=colors[i], label=chess.Board(pos).san(chess.Move.from_uci(move)))
        engine.quit()
        
    plt.legend()
    ax.set_xlim(minDepth, maxDepth)
    plt.title('Expected score for a given depth')
    ax.set_xlabel('Depth')
    ax.set_ylabel('Expected score')

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
    posMoves = [('1Q2R3/5qpk/7p/8/6P1/1p3P2/1P1r2PK/8 b - - 3 2', 'f7f3'),
                ('1Q2R3/5qpk/7p/8/6P1/1p3P2/1P1r2PK/8 b - - 3 2', 'd2b2'),
                ('1Q2R3/5qpk/7p/8/6P1/1p3P2/1P1r2PK/8 b - - 3 2', 'h7g6')]
    posMoves = [('2r3k1/5pp1/2pQr2p/p3nq2/B7/2R4P/PP3PP1/3R2K1 w - - 1 2', 'd6d8'),
                ('2r3k1/5pp1/2pQr2p/p3nq2/B7/2R4P/PP3PP1/3R2K1 w - - 1 2', 'd6d2')]
    posMoves = [('5nk1/1bq2ppp/r7/p3P3/1pp3P1/4pP1R/PPQ4P/1B1R2K1 b - - 3 26', 'c7e5'),
                ('5nk1/1bq2ppp/r7/p3P3/1pp3P1/4pP1R/PPQ4P/1B1R2K1 b - - 3 26', 'c4c3'),
                ('5nk1/1bq2ppp/r7/p3P3/1pp3P1/4pP1R/PPQ4P/1B1R2K1 b - - 3 26', 'a6g6')]
    posMoves = [('8/p2rk3/R7/P3p3/5p2/4KP2/8/8 w - - 0 2', 'e3e4'),
                ('8/p2rk3/R7/P3p3/5p2/4KP2/8/8 w - - 0 2', 'e3e2'),
                ('8/p2rk3/R7/P3p3/5p2/4KP2/8/8 w - - 0 2', 'e3f2')]
    posMoves = [('8/8/8/P1p2pp1/2P2k2/2PK1P2/r3R3/8 b - - 1 1', 'a2a5'),
                ('8/8/8/P1p2pp1/2P2k2/2PK1P2/r3R3/8 b - - 1 1', 'a2a3')]
    # plotExpectedScoreChangeByDepth(posMoves, sfConfig, 25, filename='../out/trapStalemate.png')
    poisonedPawn = chess.Board('rnb1kb1r/1p3ppp/p2ppn2/6B1/3NPP2/2N5/PqPQ2PP/R3KB1R w KQkq - 0 9')
    poisonedPawn2 = chess.Board('rnb1kb1r/1p3ppp/p2ppn2/6B1/3NPP2/q1N5/P1PQ2PP/1R2KB1R w Kkq - 2 10')
    ruyLopez = chess.Board('r1bq1rk1/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w - - 2 8')
    startPos = chess.Board()
    e4e5 = chess.Board('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2')
    e4e5Black = chess.Board('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2')
    # for position in [startPos, poisonedPawn, poisonedPawn2, ruyLopez]:
    """
    for position in [e4e5, e4e5Black]:
        sf = functions.configureEngine(*sfConfig)
        print(difficultyBR(position, sf, 18))
        sf.quit()
    """

    sfConfig = ('stockfish', {'Threads': '1', 'Hash': '1'})
    """"
    sf = functions.configureEngine(*sfConfig)
    boards = [startPos, ruyLopez, startPos]
    start = time.time()
    moveEvaluations = asyncio.run(runMultipleThreads(boards, sfConfig, 15))
    print(moveEvaluations)
    print(time.time()-start)
    start = time.time()
    for board in boards:
        analyseLegalMoves(board, sf, 15)
        print(time.time()-start)
    print(time.time()-start)
    sf.quit()
    """


    df = getTestData('../resources/bundesliga2026R3.pgn', sfConfig, 17, threads=8)
    # df = getTestData('../resources/Ding-Nepo-G12.pgn', sfConfig, 15)

    with open('../out/complexityDataD17.pkl', 'wb+') as f:
        pickle.dump(df, f)

    with open('../out/complexityDataD17.pkl', 'rb') as f:
        df = pickle.load(f)

    print(df)

    """
    testL = [[-10, 0, 30], [30, 20, 10], [10, 10, 10]]
    testL = [[-10, 30, 10], [0, 20, 10], [30, 10, 10]]
    for l in testL:
        print(absDiff(mu, l))

    print(tau(mu, testL[0], testL[1]))
    print(tau(mu, testL[1], testL[2]))


    for i in range(3):
        for d in range(3):
            print(delta(testL, i, d+1))

    print(dampenedSwing(testL, 1, 2))
    print(dampenedSwing(testL, 2, 3))

    weights = [depth/sum([d for d in range(1, 3)]) for depth in range(1, 3)]

    print(weightedSwing(testL, weights, 3))
    print(weightedSwing(testL, weights, 2))

    print(roh(testL, weights, 3))
    """


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
