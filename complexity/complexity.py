import chess
import os, sys
import math
import scipy.integrate as integrate
import asyncio
import ast

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper
import pandas as pd
import polars as pl
import statistics
import matplotlib.pyplot as plt
import pickle
import time
from scipy.stats import pearsonr
import re


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


def analyseLegalMoves(board: chess.Board, engine: chess.engine, maxDepth: int, allDepths: bool = True) -> dict:
    """
    This function analyses all legal moves in a given chess position.
    The score is for the current POV
    board: chess.Board
        The position to analyse
    engine: chess.engine
        The engine to analyse the positions with (usually SF)
    maxDepth: int
        The maximum depth for the engine analysis
    allDepths: bool
        If this is set, the moves will be analysed for all depths less than or equal to maxDepth
        Otherwise, the moves will be analysed at maxDepth
    return -> dict
        Dictionary indexed my moves with the evaluations as lists if allDepths is true or just as numbers.
        The dict is sorted from highest to lowest evaluation
    """
    moves = dict()
    for move in board.legal_moves:
        print(move.uci())
        if allDepths:
            moves[move.uci()] = list()
            for depth in range(1, maxDepth+1):
                info = engine.analyse(board, limit=chess.engine.Limit(depth=depth), root_moves=[move])
                if board.turn:
                    moves[move.uci()].append(info["score"].white().score(mate_score=1000))
                else:
                    moves[move.uci()].append(info["score"].black().score(mate_score=1000))
        else:
            info = engine.analyse(board, limit=chess.engine.Limit(depth=maxDepth), root_moves=[move])
            if board.turn:
                moves[move.uci()] = info["score"].white().score(mate_score=1000)
            else:
                moves[move.uci()] = info["score"].black().score(mate_score=1000)
        
    if allDepths:
        return dict(reversed(sorted(moves.items(), key=lambda x: x[1][-1])))
    return dict(reversed(sorted(moves.items(), key=lambda x: x[1])))


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
    if weights[e-1] * dampenedSwing(L, e, e+1) == 0:
        return 0
    return (sum(wSwingList[:e]) - 1/2 * sum(wSwingList)) / (weights[e-1] * dampenedSwing(L, e, e+1)) # different indices in the denominator than the paper, but this should be correct


def roh(L: list, weights: list, maxDepth: int) -> float:
    wSwingList = weightedSwingList(L, weights, maxDepth)
    # this calculates the minimum (which should be correct), not the maximum as stated in the paper
    for e in range(1, maxDepth):
        if sum(wSwingList[:e]) >= 1/2 * sum(wSwingList):
            finalE = e
            break

    return finalE - psiWSL(L, wSwingList, finalE, weights)


def difficultyBREngine(board: chess.Board, engine: chess.engine, maxDepth: int):
    """
    This calculates the difficulty while analysing a position
    """
    L = list(analyseLegalMoves(board, engine, maxDepth).values())
    weights = [depth/sum([d for d in range(1, maxDepth)]) for depth in range(1, maxDepth)]

    return complexityBR(L, maxDepth) * roh(L, weights, maxDepth)


def difficultyBR(L: list, maxDepth: int) -> float:
    weights = [depth/sum([d for d in range(1, maxDepth)]) for depth in range(1, maxDepth)]

    return complexityBR(L, maxDepth) * roh(L, weights, maxDepth)


def calculateEaseFromFEN(fen: str, engineEvals: chess.engine, enginePolicies: chess.engine, depth: int, expectedScoreFunction=functions.expectedScore, alpha: float = 0.333, beta: float = 1.5) -> float:
    """
    This calculates the ease metric from FEN
    fen: str
        The FEN of the position to analyse
    engineEvals: chess.engine
        The engine to get the move evaluations (usually SF)
    enginePolicies: chess.engine
        The engine to get the move policies (usually LC0 or Maia)
    depth: int
        The depth for the evaluation engine
    """
    evaluationDict = analyseLegalMoves(chess.Board(fen), engineEvals, depth, allDepths=False)
    wdl, p = lc0Analysis(fen, enginePolicies, 1)
    evaluations = list(evaluationDict.values())
    policies = [p[move] for move in evaluationDict.keys()]

    return calculateEase(evaluations, policies, expectedScoreFunction, alpha, beta)


def calculateEase(evaluations: list, policies: list, expectedScoreFunction = functions.expectedScore, alpha: float = 0.333, beta: float = 1.5) -> float:
    """
    This calculates the ease value of a position.
    Note that evaluations and policies need to be ordered by moves
    """
    total = 0
    xsMax = max([expectedScoreFunction(e) for e in evaluations])
    for i in range(len(policies)):
        total += (policies[i]/100)**beta * (xsMax - expectedScoreFunction(evaluations[i]))

    return (total/100)**alpha


def calculateSharpness(fen: str, engine: chess.engine, nodes: int) -> float:
    wdl, policies = lc0Analysis(fen, engine, nodes)
    return functions.sharpnessLC0(wdl)


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


async def analysisWorker(workerID: int, queue: asyncio.Queue, results: dict, maxDepth: int, logPath: str = None):
    while True:
        item = await queue.get()

        try:
            if item is None:
                return

            posID, fen = item
            print(queue.qsize(), workerID, fen)
            result = await analyseLegalMovesAsync(chess.Board(fen), maxDepth)

            if logPath:
                with open(f'{logPath}-{workerID}.log', 'a+') as f:
                    print(f'{fen};{result}', file=f)
            results[posID] = result

        finally:
            queue.task_done()


async def runMultipleThreads(fens: list, depth: int, nThreads: int) -> list:
    queue = asyncio.Queue()
    results = dict()

    for posID, fen in enumerate(fens):
        queue.put_nowait((posID, fen))

    logPath = '../out/compAnalysisOlympiadWorker'
    workers = [asyncio.create_task(analysisWorker(workerID, queue, results, depth, logPath=logPath)) for workerID in range(nThreads)]

    await queue.join()
    for _ in range(nThreads):
        queue.put_nowait(None)

    await asyncio.gather(*workers)
    return [result for result in sorted(results.items())]


def getTestData(pgnPath: str, engineConfig: dict, maxDepth: int, threads: int = 6, moveNumbers: list = [15, 20, 25, 30, 35, 40]) -> pl.DataFrame:
    data = dict()
    keys = ['White', 'Black', 'WhiteElo', 'BlackElo', 'FEN', 'MovePlayed']
    for key in keys:
        data[key] = list()

    # moveNumbers = [15, 20, 25, 30, 35, 40]
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

    if threads is not None:
        fens = data['FEN']
        moveEvaluations = asyncio.run(runMultipleThreads(fens, maxDepth, threads))

        data['Moves'] = [list(moves[1].keys()) for moves in sorted(moveEvaluations)]
        data['Evaluations'] = [list(moves[1].values()) for moves in sorted(moveEvaluations)]

    return pl.DataFrame(data)


def combineData(df: pl.DataFrame, analysisData: dict) -> pl.DataFrame:
    moves = list()
    evaluations = list()
    for row in df.iter_rows(named=True):
        if row['FEN'] in analysisData:
            moves.append(list(analysisData[row['FEN']].keys()))
            evaluations.append(list(analysisData[row['FEN']].values()))
        else:
            moves.append(None)
            evaluations.append(None)

    m = pl.Series('Moves', moves)
    e = pl.Series('Evaluations', evaluations)

    df.insert_column(df.shape[1], m)
    df.insert_column(df.shape[1], e)

    return df


def lc0Analysis(fen: str, lc0: chess.engine, nodes: int) -> tuple:
    """
    This function analyses a position using LC0
    return -> tuple
        (wdl: list, phead: dict)
    """
    board = chess.Board(fen)
    phead = dict()
    info = lc0.analysis(board, chess.engine.Limit(nodes=nodes))
    for i in info:
        if 'wdl' in i.keys():
            wdl = [i['wdl'].white().wins, i['wdl'].white().draws, i['wdl'].white().losses]
        elif 'string' in i.keys():
            l = list(i.values())[0]
            move = l.split()[0]
            if move == 'node':
                continue
            if board.castling_rights & chess.BB_A1 and move == 'e1a1':
                move = 'e1c1'
            elif board.castling_rights & chess.BB_H1 and move == 'e1h1':
                move = 'e1g1'
            elif board.castling_rights & chess.BB_A8 and move == 'e8a8':
                move = 'e8c8'
            elif board.castling_rights & chess.BB_H8 and move == 'e8h8':
                move = 'e8g8'
            pString = re.findall(r'P: *\d*\.\d*%', list(i.values())[0])
            p = float(pString[0].split(' ')[-1][:-1])
            phead[move] = p

    return (wdl, phead)


def lc0AnalysisDF(df: pl.DataFrame, lc0Config: tuple, nodes: int) -> pl.DataFrame:
    wdls = list()
    policies = list()
    lc0 = functions.configureEngine(*lc0Config)
    for row in df.iter_rows(named=True):
        wdl, phead = lc0Analysis(row['FEN'], lc0, nodes)
        wdls.append(wdl)
        if row['Moves'] is None:
            policies.append(None)
        else:
            pheads = list()
            for m in row['Moves']:
                if m in phead.keys():
                    pheads.append(phead[m])
                else:
                    print(f'Move not found: {m}')

            policies.append(pheads)

    lc0.quit()

    w = pl.Series('WDL', wdls)
    p = pl.Series('PHead', policies)
    df.insert_column(df.shape[1], w)
    df.insert_column(df.shape[1], p)

    return df


def calculateDifficultyForDF(df: pl.DataFrame, maxDepth: int) -> pl.DataFrame:
    difficulties = list()
    eases = list()
    sharpnesses = list()
    for row in df.iter_rows(named=True):
        sharpnesses.append(functions.sharpnessLC0(row['WDL']))
        if row['Evaluations'] is not None:
            difficulties.append(difficultyBR(row['Evaluations'], maxDepth))
            eases.append(calculateEase([e[-1] for e in row['Evaluations']], row['PHead']))
        else:
            difficulties.append(None)
            eases.append(None)

    diffs = pl.Series('DifficultyBR', difficulties)
    e = pl.Series('Ease', eases)
    s = pl.Series('Sharpness', sharpnesses)

    df.insert_column(df.shape[1], diffs)
    df.insert_column(df.shape[1], e)
    df.insert_column(df.shape[1], s)

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


def analyseDifficulty(df: pl.DataFrame):
    difficulties = list()
    eases = list()
    sharpnesses = list()
    cpls = list()
    bestMoves = list()
    ratings = list()
    for row in df.iter_rows(named=True):
        if row['DifficultyBR'] is not None:
            difficulties.append(row['DifficultyBR']/10)
            eases.append(row['Ease'])
            # sharpnesses.append(row['Sharpness']/max(row['WDL'][0], row['WDL'][2]))
            sharpnesses.append(min(row['Sharpness'], 5)/5)
            moveIndex = row['Moves'].index(row['MovePlayed'])
            bestEval = row['Evaluations'][0][-1]
            moveEval = row['Evaluations'][moveIndex][-1]
            sideToMove = row['FEN'].split()[1]
            if sideToMove == 'w':
                ratings.append(int(row['WhiteElo']))
            elif sideToMove == 'b':
                ratings.append(int(row['BlackElo']))
            if moveIndex == 0:
                bestMoves.append(True)
            else:
                bestMoves.append(False)
            cpls.append(functions.expectedScore(bestEval)-functions.expectedScore(moveEval))

    indices = [i for i in range(len(cpls)) if cpls[i] != 0 and ratings[i] >= 2500]
    print(len(indices))
    for values in [difficulties, eases, sharpnesses]:
        print(pearsonr([values[i] for i in indices], [cpls[i] for i in indices]))

    # plotting_helper.plotScatterPlot([cpls]*3, [difficulties, eases, sharpnesses], 'Expected score loss', 'Difficulty', 'Difficulty vs XS loss', legend=['Difficulty', 'Ease', 'Sharpness'], alpha=0.5)
    plotting_helper.plotScatterPlot([[cpls[i] for i in indices]]*3, [[difficulties[i] for i in indices], [eases[i] for i in indices], [sharpnesses[i] for i in indices]], 'Expected score loss', 'Difficulty', 'Difficulty vs XS loss', legend=['Difficulty', 'Ease', 'Sharpness'], alpha=0.5)
    
    diffData = dict()
    for i in range(15):
        diffData[i/2+0.5] = [0, 0, 0]

    for i, diff in enumerate(difficulties):
        if ratings[i] < 2400:
            continue
        index = 7.5
        for j in diffData.keys():
            if diff < j:
                index = j
                break

        diffData[index][1] += cpls[i]
        diffData[index][2] += 1
        if bestMoves[i]:
            diffData[index][0] += 1

    plotData = list()
    for k, v in diffData.items():
        print(k, v[0]/max(1, v[2]), v[1]/max(1, v[2]), v[2])
        plotData.append([v[1]/max(1, v[2])])

    # plotting_helper.plotScatterPlot([difficulties], [cpls], 'Difficulty', 'Expected score loss', 'Difficulty vs XS loss')
    # plotting_helper.plotPlayerBarChart(plotData, list(diffData.keys()), 'Expected score loss', 'Expected score loss by difficulty of the position', ['XSL'], xlabel='Difficulty')


def testComplexityFunctions(compFunctions: list):
    startPos = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    for compFunc in compFunctions:
        print(f'Complexity of start position: {compFunc(startPos)}')


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
    """
    poisonedPawn = chess.Board('rnb1kb1r/1p3ppp/p2ppn2/6B1/3NPP2/2N5/PqPQ2PP/R3KB1R w KQkq - 0 9')
    poisonedPawn2 = chess.Board('rnb1kb1r/1p3ppp/p2ppn2/6B1/3NPP2/q1N5/P1PQ2PP/1R2KB1R w Kkq - 2 10')
    ruyLopez = chess.Board('r1bq1rk1/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w - - 2 8')
    startPos = chess.Board()
    e4e5 = chess.Board('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2')
    e4e5Black = chess.Board('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2')
    """
    # for position in [startPos, poisonedPawn, poisonedPawn2, ruyLopez]:
    """
    for position in [e4e5, e4e5Black]:
        sf = functions.configureEngine(*sfConfig)
        print(difficultyBR(position, sf, 18))
        sf.quit()
    """

    sfConfig = ('stockfish', {'Threads': '1', 'Hash': '1'})

    # sf = functions.configureEngine(*sfConfig)
    # This position doesn't work for the move e2e4
    # print(analyseLegalMoves(chess.Board('1r2k1r1/pq3p1p/4pB2/3pP2R/Rn4P1/8/4QP2/4K3 w - - 0 30'), sf, 19))

    # df = getTestData('../resources/bundesliga2026R1-2.pgn', sfConfig, 19, threads=8)
    # df = getTestData('../resources/Ding-Nepo-G12.pgn', sfConfig, 15)

    """
    with open('../out/complexityDataD19.pkl', 'wb+') as f:
        pickle.dump(df, f)

    with open('../out/complexityDataD19.pkl', 'rb') as f:
        df = pickle.load(f)
    """

    # print(df)
    # sf.quit()

    lc0Config = ('lc0', {'WeightsFile': '/home/julian/Desktop/weights2026.gz', 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})
    lc0Config = ('lc0', {'WeightsFile': '/Users/julian/chess/nets/largeNet', 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})

    """
    sf = functions.configureEngine(*sfConfig)
    lc0 = functions.configureEngine(*lc0Config)
    complexityFunctions = [lambda fen: difficultyBREngine(chess.Board(fen), sf, 19), lambda fen: calculateEaseFromFEN(fen, sf, lc0, 19), lambda fen: calculateSharpness(fen, lc0, 10000)]
    testComplexityFunctions(complexityFunctions)

    sf.quit()
    lc0.quit()
    """

    outFile = '../out/complexityOlympiadD19Analysed-R6-11.pkl'
    outFile = '../out/complexityOlympiadD19Analysed-R4-5.pkl'
    # Combining all analysis data
    """
    df = None
    for pgn in ['../resources/olympiad2026-R6.pgn', '../resources/olympiad2026-R7-8.pgn', '../resources/olympiad2026-R9-10.pgn', '../resources/olympiad2026-R11.pgn']:
        if df is None:
            df = getTestData(pgn, sfConfig, 19, threads=None)
        else:
            if pgn.split('-')[1][:3] == 'R11':
                df1 = getTestData(pgn, sfConfig, 19, threads=None, moveNumbers=[15, 35, 40])
            else:
                df1 = getTestData(pgn, sfConfig, 19, threads=None)
            df = pl.concat([df, df1])

    print(df)
    with open(outFile, 'wb+') as f:
        pickle.dump(df, f)

    with open(outFile, 'rb') as f:
        df = pickle.load(f)
    """

    
    # Combining analysed data from the logs with the DF
    """
    analysisData = dict()
    for i in range(10):
        with open(f'../out/compAnalysisOlympiadWorker-{i}.log', 'r') as f:
            for line in f.readlines():
                fen = line.split(';')[0]
                moveData = ast.literal_eval(line.split(';')[1])
                analysisData[fen] = moveData

    """
    pgn = '../resources/olympiad2026-R4-5.pgn'
    df = getTestData(pgn, sfConfig, 19, threads=10)
    # df = getTestData(pgn, sfConfig, 19, threads=None)
    # df = combineData(df, analysisData)
    # df = calculateDifficultyForDF(df, 19)
    with open(outFile, 'wb+') as f:
        pickle.dump(df, f)

    with open(outFile, 'rb') as f:
        df = pickle.load(f)

    print(df)

    """
    # Adding information deleted from the Logs
    with open('../out/complexityOlympiadD19Analysed.pkl', 'rb') as f:
        df = pl.concat([df, pickle.load(f)])

    print(df)

    with open(outFile, 'wb+') as f:
        pickle.dump(df, f)

    """

    outFile2 =  '../out/complexityOlympiadD19Analysed-R6-11-diff.pkl'
    """
    df = calculateDifficultyForDF(df, 19)

    with open(outFile2, 'wb+') as f:
        pickle.dump(df, f)
    """

    """
    with open(outFile2, 'rb') as f:
        df = pickle.load(f)

    analyseDifficulty(df)
    """

    """
    df = lc0AnalysisDF(df, lc0Config, 10000)
    print(df)
    with open(outFile, 'wb+') as f:
        pickle.dump(df, f)
    """

    """
    with open('../out/complexityDataD19Analysed-3.pkl', 'rb') as f:
        df = pickle.load(f)
    print(df)
    df = df.drop('Difficulty')
    df = calculateDifficultyForDF(df, 19)
    print(df)
    with open('../out/complexityDataD19Analysed-3.pkl', 'wb+') as f:
        pickle.dump(df, f)
    """

    """
    with open('../out/complexityDataD19Analysed-3.pkl', 'rb') as f:
        df = pickle.load(f)

    print(df)
    """
