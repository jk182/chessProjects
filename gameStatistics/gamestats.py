import chess
from chess import pgn
import pandas as pd
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import evalDB
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy import integrate
import numpy as np
import scipy
import plotting_helper


def readMoveData(pgnPaths: list, is_chess960: bool = False, lichessAnalysis: bool = False) -> pd.DataFrame:
    """
    This function reads the move data from annotated PGN files and returns a dataframe with data about each move
    """
    startEval = 20
    startWDL = [205, 614, 181]
    columns = ["GameID", "Position", "Color", "Move", "MoveNr", "WhiteElo", "BlackElo", "EvalBefore", "EvalAfter", "WinPBefore", "DrawPBefore", "LossPBefore", "WinPAfter", "DrawPAfter", "LossPAfter", "Result"]
    data = dict()
    gameID = 0
    for c in columns:
        data[c] = list()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                    print("No Elo")
                    continue
                ply = 1
                wElo = int(game.headers["WhiteElo"])
                bElo = int(game.headers["BlackElo"])
                result = game.headers["Result"]

                if is_chess960:
                    board = game.board()
                    pos = board.fen()
                    posDB = functions.modifyFEN(pos)
                    evalBefore = None
                    wdlBefore = None
                    
                    if evalDB.contains(posDB):
                        evalDict = evalDB.getEval(posDB)
                        wdl = evalDict['wdl']
                        cp = evalDict['cp']
                        if evalDict['depth'] > 0 and evalDict['nodes'] > 0:
                            evalBefore = cp
                            wdlBefore = wdl
                        else:
                            # TODO!
                            print('Not found in cache')
                    if not evalDB.contains(posDB) or evalBefore is None or wdlBefore is None or type(evalBefore) is not int:
                        # TODO!
                        print('Analysing position...')
                        op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'}
                        leela = functions.configureEngine('lc0', op)
                        sf = functions.configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
                        LC0Info = leela.analyse(board, chess.engine.Limit(nodes=10000))
                        wdl = list(chess.engine.PovWdl.white(LC0Info['wdl']))
                        sfInfo = sf.analyse(board, chess.engine.Limit(time=4))
                        cp = sfInfo['score'].white().score()
                        print(cp)
                        if evalDB.contains(posDB) or type(evalBefore) is not int:
                            evalDB.update(posDB, nodes=10000, cp=cp, w=wdl[0], d=wdl[1], l=wdl[2], depth=sfInfo['depth'])
                        else:
                            evalDB.insert(posDB, nodes=10000, cp=cp, w=wdl[0], d=wdl[1], l=wdl[2], depth=sfInfo['depth'])
                        sf.quit()
                        leela.quit()

                        evalBefore = cp
                        wdlBefore = wdl
                else:
                    evalBefore = startEval
                    wdlBefore = startWDL

                node = game
                while not node.is_end():
                    board = node.board()
                    node = node.variations[0]
                    ply += 1
                    if node.comment:
                        if lichessAnalysis:
                            if not node.eval():
                                break
                            cp = int(node.eval().white().score(mate_score=10000))
                            wdl = [0, 0, 0]
                        else:
                            wdl, cp = functions.readComment(node, True, True)
                        move = node.move
                        data["GameID"].append(gameID)
                        data["Color"].append(board.turn)
                        data["WhiteElo"].append(wElo)
                        data["BlackElo"].append(bElo)
                        data["Result"].append(result)
                        data["Position"].append(board.fen())
                        data["EvalBefore"].append(evalBefore)
                        data["WinPBefore"].append(wdlBefore[0])
                        data["DrawPBefore"].append(wdlBefore[1])
                        data["LossPBefore"].append(wdlBefore[2])
                        data["EvalAfter"].append(cp)
                        data["WinPAfter"].append(wdl[0])
                        data["DrawPAfter"].append(wdl[1])
                        data["LossPAfter"].append(wdl[2])
                        data["Move"].append(move.uci())
                        data["MoveNr"].append(ply//2)
                        evalBefore = cp
                        wdlBefore = wdl
                gameID += 1
    df = pd.DataFrame(data)
    return df


def filterGamesByRating(df: pd.DataFrame, ratingRange: tuple, ratingDifference: int, bothPlayers: bool = False) -> pd.DataFrame:
    """
    This filters a dataframe to only include games with the specified rating.
    df: pd.DataFrame
        The dataframe with the move data
    ratingRange: tuple
        Minimum and maximum rating for one of these players
    ratingDifference: int
        The maximal difference in rating between these players
    bothPlayers: bool
        If set, both players will be in the rating range, without considering the difference
    return -> pd.DataFrame
        Dataframe with only the games where players are in the rating range
    """
    minElo, maxElo = ratingRange
    if not bothPlayers:
        filtered = df[(abs(df["WhiteElo"]-df["BlackElo"]) <= ratingDifference) & (((minElo <= df["WhiteElo"]) & (df["WhiteElo"] <= maxElo)) | ((minElo <= df["BlackElo"]) & (df["BlackElo"] <= maxElo)))]
    else:
        filtered = df[(minElo <= df["WhiteElo"]) & (df["WhiteElo"] <= maxElo) & (minElo <= df["BlackElo"]) & (df["BlackElo"] <= maxElo)]
    filtered = filtered.reset_index()
    return filtered


def getExpectedScore(df: pd.DataFrame, cpCutoff: int) -> float:
    """
    This calculates the win percentage when one side has an advantage of cpCutoff
    """
    wins = df[((df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1-0")) | ((df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "0-1"))]
    draws = df[(abs(df["EvalAfter"]) >= cpCutoff) & (df["Result"] == "1/2-1/2")]
    games = df[abs(df["EvalAfter"]) >= cpCutoff]

    """
    whiteWins = df[(df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1-0")]
    blackWins = df[(df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "0-1")]
    whiteDraws = df[(df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1/2-1/2")]
    blackDraws = df[(df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "1/2-1/2")]
    whiteGames = df[df["EvalAfter"] >= cpCutoff]
    blackGames = df[df["EvalAfter"] <= -cpCutoff]
    """
    whiteWins = df[(df["EvalAfter"] >= cpCutoff) & (df["EvalAfter"] <= cpCutoff+50) & (df["Result"] == "1-0")]
    blackWins = df[(df["EvalAfter"] <= -cpCutoff) & (df["EvalAfter"] >= -cpCutoff-50) & (df["Result"] == "0-1")]
    whiteDraws = df[(df["EvalAfter"] >= cpCutoff) & (df["EvalAfter"] <= cpCutoff+50) & (df["Result"] == "1/2-1/2")]
    blackDraws = df[(df["EvalAfter"] <= -cpCutoff) & (df["EvalAfter"] >= -cpCutoff-50) & (df["Result"] == "1/2-1/2")]
    whiteGames = df[(df["EvalAfter"] >= cpCutoff) & (df["EvalAfter"] <= cpCutoff+50)]
    blackGames = df[(df["EvalAfter"] <= -cpCutoff) & (df["EvalAfter"] >= -cpCutoff-50)]

    nWins = len(set(wins["GameID"]))
    nDraws = len(set(draws["GameID"]))
    nGames = len(set(games["GameID"]))

    nWhiteWins = len(set(whiteWins["GameID"]))
    nBlackWins = len(set(blackWins["GameID"]))
    nWhiteDraws = len(set(whiteDraws["GameID"]))
    nBlackDraws = len(set(blackDraws["GameID"]))
    nWhiteGames = len(set(whiteGames["GameID"]))
    nBlackGames = len(set(blackGames["GameID"]))
    # return ((nWhiteWins + 0.5*nWhiteDraws)/nWhiteGames, (nBlackWins + 0.5*nBlackDraws)/nBlackGames)
    return ((nWhiteWins + 0.5*nWhiteDraws)+ (nBlackWins + 0.5*nBlackDraws))/(nWhiteGames+nBlackGames)


def winPLichess(cp: int, k: float) -> float:
    """
    This calculates the win percentage with the formula used by Lichess
    """
    return 100/(1+math.exp(-k*cp))


def expectedScore(cp: int, k: float) -> float:
    return 50+100/math.pi * math.atan(k*cp)


def plotExpectedScore(points: list, functions: list, labels: list, title: str, filename: str = None):
    """
    This function plots the given points and functions
    """
    maxEval = 1000
    xRange = [i for i in range(-maxEval-100, maxEval+101)]
    colors = ['#689bf2', '#C3B1E1', '#f8a978', '#fa5a5a', '#5afa8d']
    fig, ax = plt.subplots(figsize=(10,6))
    ax.set_facecolor('#e6f7f2')
    
    xes = [p[0] for p in points]
    ys = [p[1] for p in points]

    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)
    ax.grid(zorder=0)

    ax.scatter(xes, ys, color=colors[0], label='Avg score in GM games', zorder=3, edgecolor='blue')
    
    for i, (function, parameter) in enumerate(functions):
        ax.plot(xRange, [function(x, parameter) for x in xRange], color=colors[i+1], label=labels[i], linewidth=3)

    ax.legend()
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.xlim(-maxEval*1.05, maxEval*1.05)
    ax.set_xlabel('Centipawn advantage')
    ax.set_ylabel('Expected score')
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.title(title)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getExpectedScoreDrop(df: pd.DataFrame, function: tuple, minMove: int = 0) -> dict:
    """
    This function calculates the percentage of moves where the expected score drops a specific amount.
    df: pd.DataFrame
        Containing the move data
    function: tuple
        The function together with the parameter to calculate the expected score
    minMove: int
        The least move number to be considered to exclude opening moves
    """
    f, k = function
    drops = dict()
    total = 0
    for i, row in df.iterrows():
        if row["MoveNr"] < minMove:
            continue
        total += 1
        if row["Color"] == chess.WHITE:
            esb = f(row["EvalBefore"], k)
            esa = f(row["EvalAfter"], k)
        else:
            esb = -f(row["EvalBefore"], k)
            esa = -f(row["EvalAfter"], k)
        drop = max(0, esb-esa)
        # drop = esb-esa
        # drop = int(drop)
        drop = round(drop, 2)
        if drop in drops.keys():
            drops[drop] += 1
        else:
            drops[drop] = 1

    for k in drops.keys():
        drops[k] /= total
    return drops


def getGameExpectedScoreDrops(df: pd.DataFrame, function: tuple = (expectedScore, 0.007851), minMove: int = 0) -> dict:
    """
    This fucntion calculates the average expected score drops for each game.
    """
    f, k = function
    drops = dict()
    lastGameID = None
    gameDrops = dict()
    totalDrops = [0, 0]
    moves = [0, 0]
    for i, row in df.iterrows():
        currentGameID = row["GameID"]
        if lastGameID is None:
            lastGameID = currentGameID
        if lastGameID != currentGameID:
            lastGameID = currentGameID
            for i in [0, 1]:
                avgDrop = totalDrops[i]/moves[i]
                avgDrop = round(avgDrop, 2)
                if avgDrop in gameDrops.keys():
                    gameDrops[avgDrop] += 1
                else:
                    gameDrops[avgDrop] = 1
            totalDrops = [0, 0]
            moves = [0, 0]
        if row["Color"] == chess.WHITE:
            esb = f(row["EvalBefore"], k)
            esa = f(row["EvalAfter"], k)
            index = 0
        else:
            esb = -f(row["EvalBefore"], k)
            esa = -f(row["EvalAfter"], k)
            index = 1
        drop = max(0, esb-esa)
        totalDrops[index] += drop
        moves[index] += 1
    for i in [0, 1]:
        avgDrop = totalDrops[i]/moves[i]
        avgDrop = round(drop, 2)
        if avgDrop in gameDrops.keys():
            gameDrops[avgDrop] += 1
        else:
            gameDrops[avgDrop] = 1
    totalGames = sum(gameDrops.values())
    for k in gameDrops.keys():
        gameDrops[k] /= totalGames
    return gameDrops


def plotAccuracyDistribution(gameDrops: dict, filename: str = None):
    """
    This function plots the data from getGameExpectedScoreDrops as a distribution
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#689bf2', '#C3B1E1', '#f8a978', '#fa5a5a', '#5afa8d']
    ax.set_facecolor('#e6f7f2')
    lists = sorted(gameDrops.items())
    keys, values = zip(*lists)
    width = (max(keys)-min(keys))/len(keys)
    plt.bar(keys, values, alpha=1, width=width, color=colors[0])
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    ax.set_xlabel('Avg Expected Score loss per move')
    ax.set_ylabel('Relative number of games')
    ax.set_xlim(0, max(keys)*1.02)
    plt.title('Distribution of avg expected score loss per move')
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getCumulativeDrop(drops: dict):
    cumulative = dict()
    for key in drops.keys():
        cumulative[key] = sum([v for k,v in drops.items() if k >= key])
    return cumulative


def filterDataByGameMoves(df: pd.DataFrame, minMove: int, maxMove: int) -> pd.DataFrame:
    """
    This function returns a dataframe where only moves of games in the specified move range are considered
    """
    allowedIDs = list()
    lastGameID = None
    move = 0
    for i, row in df.iterrows():
        cGameID = row["GameID"]
        if lastGameID is None:
            lastGameID = cGameID
        if lastGameID != cGameID:
            if minMove <= move <= maxMove:
                allowedIDs.append(lastGameID)
            lastGameID = cGameID
        else:
            move = row["MoveNr"]
    newDf = df[df["GameID"].isin(allowedIDs)]
    newDf = newDf.reset_index()
    return newDf


def accuracyLichess(winPB: float, winPA: float, start: float, k: float) -> float:
    return start * math.exp(-k * (winPB - winPA)) + (100-start)


def genGamma(t, x, l):
    return np.exp(-t)*t**(x-1)


def gammaInt(x, l):
    upper = np.inf
    return integrate.quad(genGamma, l, upper, args=(x,l))[0]


def logistic(a, x):
    return 1 / (1+np.exp((-a*x)))


def getDerivative(data: dict) -> dict:
    """
    This calculates the slopes between datapoints in the dictionary
    """
    lists = sorted(data.items())
    keys, values = zip(*lists)
    derivative = dict()
    for i in range(len(keys)-1):
        derivative[keys[i]] = (values[i+1]-values[i])/(keys[i+1]-keys[i])
    return derivative


def plotAccuracies(dropList: list, labels: list, title: str, axisLabels: tuple, colors: list = None, filename: str = None):
    fig, ax = plt.subplots(figsize=(10, 6))
    if not colors:
        colors = ['#f8a978', '#689bf2', '#fa5a5a', '#C3B1E1', '#5afa8d']
    ax.set_facecolor('#e6f7f2')
    # ax.set_yscale("log")
    maxX = 0
    for i, drops in enumerate(dropList):
        lists = sorted(drops.items())
        x, y = zip(*lists)
        maxX = max(max(x), maxX)
        plt.plot(x, [100*(1-i) for i in y], color=colors[i%len(colors)], label=labels[i])
    mu = 1.965
    sigma = 0.9
    xr = [c/100 for c in range(0, 800)]
    # plt.plot(xr, [1-(1/2*(1+math.erf((x-mu)/(sigma*math.sqrt(2))))) for x in xr])

    lmb = 1.5
    npRange = np.arange(0, 8, 0.1)
    contPoisson = [1-scipy.special.gammaincc(x-0.4, lmb) for x in npRange]
    # plt.plot(npRange, contPoisson)
    """
    for a in [1.5, 1.7, 2, 2.2]:
        plt.plot(npRange, [1-logistic(a, x-mu) for x in npRange], label=a)
    """

    derivative = getDerivative(dropList[0])
    lists = sorted(derivative.items())
    x, y = zip(*lists)
    # plt.plot(x, y)
    # plt.plot(range(0, 50), [accuracyLichess(x, 0, 103.1668, 0.04354)/100 for x in range(0, 50)])
    
    sigma = 1.55
    offset = 0.25
    ray = [100*np.exp(-(x-offset)**2/(2*sigma**2)) if x > offset else 100 for x in npRange]
    # plt.plot(npRange, ray, color=colors[1], label='Accuracy score')

    ax.set_xlim(0, 6.2)
    ax.set_ylim(-0.2, 100.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.legend()
    ax.set_xlabel(axisLabels[0])
    ax.set_ylabel(axisLabels[1])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.title(title)
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getxScoreDropByMoves(moveData: pd.DataFrame) -> dict:
    """
    This calculates the expected score drop depending on the move number
    """
    moveDrops = dict()
    for i, row in moveData.iterrows():
        moveNr = row["MoveNr"]
        if row["Color"]:
            xs = (functions.expectedScore(row["EvalBefore"]), functions.expectedScore(row["EvalAfter"]))
        else:
            xs = (functions.expectedScore(-row["EvalBefore"]), functions.expectedScore(-row["EvalAfter"]))
        score = max(0, xs[0]-xs[1])
        if moveNr in moveDrops.keys():
            moveDrops[moveNr].append(score)
        else:
            moveDrops[moveNr] = [score]
    return moveDrops


def getxScoreDropByEval(moveData: pd.DataFrame) -> dict:
    evalDrops = dict()
    for i, row in moveData.iterrows():
        if row["Color"]:
            xs = (functions.expectedScore(row["EvalBefore"]), functions.expectedScore(row["EvalAfter"]))
            evalB = row["EvalBefore"]
            # evalB = xs[0]
        else:
            xs = (functions.expectedScore(-row["EvalBefore"]), functions.expectedScore(-row["EvalAfter"]))
            evalB = -row["EvalBefore"]
            # evalB = xs[0]
        score = max(0, xs[0]-xs[1])
        evalB = (evalB // 10) * 10
        if evalB in evalDrops.keys():
            evalDrops[evalB].append(score)
        else:
            evalDrops[evalB] = [score]
    return evalDrops


def getxScoreDrops(moveData: pd.DataFrame) -> dict:
    drops = dict()
    total = 0
    for i, row in moveData.iterrows():
        if row["Color"]:
            xs = (functions.expectedScore(row["EvalBefore"]), functions.expectedScore(row["EvalAfter"]))
        else:
            xs = (functions.expectedScore(-row["EvalBefore"]), functions.expectedScore(-row["EvalAfter"]))
        score = round(max(0, xs[0]-xs[1]), 0)
        total += 1
        if score in drops.keys():
            drops[score] += 1
        else:
            drops[score] = 1
    for k, v in drops.items():
        drops[k] = v/total
    return drops


def getClockTimes(pgnPaths: list, minutes: bool = True) -> list:
    """
    This calculates the clock times on every move for White and Black
    minutes: bool
        If this is set, the time will be given in minutes
    return -> list
        A list of lists of lists:
            Each color has a list which contains a list per game with the time after each move
    """
    times = [list(), list()]
    
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                whiteTimes = list()
                blackTimes = list()

                node = game
                while not node.is_end():
                    node = node.variations[0]
                    if not node.clock():
                        print("No time read")
                        if minutes:
                            time *= 60
                    else:
                        time = int(node.clock())
                    if minutes:
                        time /= 60
                    if not node.turn():
                        whiteTimes.append(time)
                    else:
                        blackTimes.append(time)
                times[0].append(whiteTimes)
                times[1].append(blackTimes)
    return times


def plotAvgTime(clockTimes: list, title: str, startTime: int = 90, maxMoves: int = 39, filename: str = None):
    colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    
    yMin = 0
    yMax = 0
    for k, d in enumerate(clockTimes):
        avg = [startTime]
        for i in range(maxMoves):
            l = [c[i] for c in d if len(c) > i]
            if len(l) == 0:
                break
            avg.append(sum(l)/len(l))
        ax.plot(range(0, maxMoves+1), avg, color=colors[k])
        yMin = min(yMin, min(avg))
        yMax = max(yMax, max(avg))
    
    plt.xlim(0, maxMoves)
    plt.ylim(yMin*1.05, yMax*1.05)
    ax.set_xlabel('Move Number')
    ax.set_ylabel('Time remaining in minutes')
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotBarChart(data: dict, xLabel: str, yLabel: str, title: str, width: int = 1, y_log: bool = False, isList: bool = True, limits: list = None, data2: dict = None, filename: str = None):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#f8a978', '#689bf2', '#fa5a5a', '#C3B1E1', '#5afa8d']
    ax.set_facecolor('#e6f7f2')
    if isList:
        nData = dict()
        for k, v in data.items():
            if abs(k) > 500:
                continue
            n = 0
            for drop in v:
                if drop > 10:
                    n += 1
            nData[k] = n/len(v)
            # nData[k] = sum(v)/len(v)
    else:
        nData = data

    if data2:
        ax.bar([x-width/4 for x in list(nData.keys())], list(nData.values()), color=colors[0], width=width/2, edgecolor='black', label='Classical accuracy')
        ax.bar([x+width/4 for x in list(data2.keys())], list(data2.values()), color=colors[1], width=width/2, edgecolor='black', label='Chess 960 accuracy')
        ax.legend()
    else:
        ax.bar(list(nData.keys()), list(nData.values()), color=colors[1], width=width, edgecolor='black')

    if y_log:
        ax.set_yscale('log')

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    if limits:
        ax.set_xlim(*limits)
    plt.title(title)
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getInaccMistakesBlunders(drops: list, imbValues: list = [5, 10, 15]) -> list:
    """
    This calculates the relative number of inaccuracies, mistakes and blunders given the drops in expected score
    drops: list
        A list of lists containing the drops
    imb: list
        The cutoff points for inaccuracies, mistakes and blunders
    return -> list
        A list with the relative number of inaccuracies, mistakes and blunders for each of the drops
    """
    imb = list()
    for d in drops:
        current = [0, 0, 0]
        for drop, relAmount in d.items():
            if drop < imbValues[0]:
                continue
            for i, v in enumerate(imbValues):
                if (i < 2 and drop <= imbValues[i+1] and drop > imbValues[i]) or (i == 2 and drop > imbValues[i]):
                    current[i] += relAmount
                    break
        imb.append(current)
    return imb


if __name__ == '__main__':
    pgns = ['../out/games/2700games2023-out.pgn', '../out/games/olympiad2024-out.pgn', '../out/games/grenkeOpen2024.pgn', '../out/games/wijkMasters2024-5000-30.pgn', '../out/games/shenzhen-5000-30.pgn', '../out/games/norwayChessClassical.pgn', '../out/games/candidates2024-WDL+CP.pgn', '../out/games/tepe-sigeman-5000-30.pgn', '../out/games/gukesh2022-out.pgn', '../out/games/Norway2021-classical.pgn', '../out/games/arjun_open-5000-30.pgn', '../out/games/bundesliga2500-out.pgn']
    pgns960 = ['../out/games/grenke960-analysed.pgn', '../out/games/paris960-analysed.pgn',  '../out/games/germany960_2024-analysed.pgn',   '../out/games/germany960_2024-analysed.pgn']
    pgns960Clocks = ['../resources/grenke960.pgn', '../resources/paris960.pgn',  '../resources/germany960_2024.pgn',   '../resources/germany960_2024.pgn']
    """
    clockTimes = getClockTimes(pgns960Clocks)
    plotAvgTime(clockTimes, 'Remaining time per move in chess 960')
    clockTimes = getClockTimes(['../resources/sharjah_clocks.pgn'])
    plotAvgTime(clockTimes, 'Remaining time per move in classical chess')
    """
    # df = readMoveData(pgns960, True)
    # df.to_pickle('../out/chess960DF')
    
    classical = ['../resources/germanBundesliga2025.pgn', '../resources/candidatesL.pgn', '../resources/olympiad2024.pgn', '../resources/wijk2025.pgn', '../resources/grandSwiss2023.pgn', '../resources/sharjah2024.pgn', '../resources/sharjah2025.pgn']
    # classicalDF = readMoveData(classical, lichessAnalysis=True)
    # classicalDF.to_pickle('../out/classicalDF')
    classicalDF = pd.read_pickle('../out/classicalDF')
    

    blitz = ['../resources/worldBlitz2023.pgn', '../resources/worldBlitz2024.pgn', '../resources/worldBlitz2022.pgn', '../resources/teamBlitz2025.pgn']
    # blitzDF = readMoveData(blitz, lichessAnalysis=True)
    # blitzDF.to_pickle('../out/blitzDF')

    blitzDF = pd.read_pickle('../out/blitzDF')

    rapid = ['../resources/worldRapid2023.pgn', '../resources/worldRapid2024.pgn', '../resources/worldRapid2022.pgn', '../resources/teamRapid2025.pgn']
    # rapidDF = readMoveData(rapid, lichessAnalysis=True)
    # rapidDF.to_pickle('../out/rapidDF')
    rapidDF = pd.read_pickle('../out/rapidDF')

    bGM = filterGamesByRating(blitzDF, (2500, 3000), 150, True)
    rGM = filterGamesByRating(rapidDF, (2500, 3000), 150, True)
    cGM = filterGamesByRating(classicalDF, (2500, 3000), 150, True)

    # Inaccuracies, mistakes, blunders
    cGMdrops = getxScoreDrops(cGM)
    bGMdrops = getxScoreDrops(bGM)
    rGMdrops = getxScoreDrops(rGM)
    # imb = getInaccMistakesBlunders([bGMdrops, rGMdrops, cGMdrops])
    # plotting_helper.plotPlayerBarChart(imb, ['Blitz', 'Rapid', 'Classical'], 'Relative number of moves', 'Relative number of inaccuracies, mistakes and blunders in different time controls', ['Inaccuracies', 'Mistakes', 'Blunders'], colors=plotting_helper.getColors(['blue', 'yellow', 'red']), filename='../out/rapidBlitz/imb.png')

    # Accuracy for all GMs
    blitzGameDrops = getGameExpectedScoreDrops(bGM)
    CBGD = getCumulativeDrop(blitzGameDrops)
    rapidGameDrops = getGameExpectedScoreDrops(rGM)
    CRGD = getCumulativeDrop(rapidGameDrops)
    classicalGameDrops = getGameExpectedScoreDrops(cGM)
    CCGD = getCumulativeDrop(classicalGameDrops)

    print(max([k for k,v in CBGD.items() if v >= 0.5]), max([k for k,v in CRGD.items() if v >= 0.5]), max([k for k,v in CCGD.items() if v >= 0.5]))

    plotAccuracies([CBGD, CRGD, CCGD], ['Blitz', 'Rapid', 'Classical'], 'Game accuracy in different time controls', ('Maximum expected score loss per move', 'Percentage of games'), colors=plotting_helper.getColors(['violet', 'blue', 'orange']), filename='../out/rapidBlitz/accuracyGM.png')

    # Ratings
    blitz2500 = filterGamesByRating(blitzDF, (2500, 2700), 100, False)
    blitz2700 = filterGamesByRating(blitzDF, (2700, 3000), 100, False)
    bDrops25 = getGameExpectedScoreDrops(blitz2500, (expectedScore, 0.007851))
    cbd25 = getCumulativeDrop(bDrops25)
    bDrops27 = getGameExpectedScoreDrops(blitz2700, (expectedScore, 0.007851))
    cbd27 = getCumulativeDrop(bDrops27)

    rapid2500 = filterGamesByRating(rapidDF, (2500, 2700), 100, False)
    rapid2700 = filterGamesByRating(rapidDF, (2700, 3000), 100, False)
    rDrops25 = getGameExpectedScoreDrops(rapid2500, (expectedScore, 0.007851))
    crd25 = getCumulativeDrop(rDrops25)
    rDrops27 = getGameExpectedScoreDrops(rapid2700, (expectedScore, 0.007851))
    crd27 = getCumulativeDrop(rDrops27)

    """
    classical2500 = filterGamesByRating(classicalDF, (2500, 2700), 100, False)
    classical2700 = filterGamesByRating(classicalDF, (2700, 2900), 100, False)
    cDrops25 = getGameExpectedScoreDrops(classical2500, (expectedScore, 0.007851))
    ccd25 = getCumulativeDrop(cDrops25)
    cDrops27 = getGameExpectedScoreDrops(classical2700, (expectedScore, 0.007851))
    ccd27 = getCumulativeDrop(cDrops27)
    """

    plotAccuracies([cbd25, cbd27, crd25, crd27], ['2500-2700 Blitz', '2700+ Blitz', '2500-2700 Rapid', '2700+ Rapid'], 'Game accuracy in rapid and blitz for different rating ranges', ('Maximum expected score loss per move', 'Percentage of games'), colors=plotting_helper.getColors(['violet', 'blue', 'orange', 'red']), filename='../out/rapidBlitz/accuracyRatings.png')
    # plotAccuracies([cDrops2700, cDrops2600, cDrops2500, cbDrops, crDrops], ['2700', '2600', '2500', 'Blitz', 'Rapid'], 'Move accuracy', ('Expected score loss', 'Percentage of moves'))


    """
    # Blitz games post
    blitzDF = pd.read_pickle('../out/blitzDF')
    drops = getxScoreDrops(blitzDF)
    cDrops = getCumulativeDrop(drops)

    rapidDF = pd.read_pickle('../out/rapidDF')
    rDrops = getxScoreDrops(rapidDF)
    crDrops = getCumulativeDrop(rDrops)

    df = pd.read_pickle('../out/gameDF')
    dfGM = filterGamesByRating(df, (2500, 2900), 150, True)
    dropsClassical = getxScoreDrops(dfGM)
    cdc = getCumulativeDrop(dropsClassical)
    imb = getInaccMistakesBlunders([drops, rDrops, dropsClassical])
    plotting_helper.plotPlayerBarChart(imb, ['Blitz', 'Rapid', 'Classical'], 'Relative number of moves', 'Relative number of inaccuracies, mistakes and blunders in different time controls', ['Inaccuracies', 'Mistakes', 'Blunders'])
    # plotAccuracies([cDrops, crDrops, cdc], ["Blitz", "Rapid", "Classical"], 'Move Accuracy', ('Expected score loss', 'Percentage of moves'))
    """

    """
    GM mistakes post
    df = pd.read_pickle('../out/chess960DF')
    dfGM = filterGamesByRating(df, (2500, 2900), 150, True)
    xScoreMoves = getxScoreDropByMoves(dfGM)
    plotBarChart(xScoreMoves, 'Move number', 'Relative number of mistakes', 'Relative number of mistakes every move in chess 960', limits=[0.5, 85], filename='../out/moveNrMistakes.png')
    xScoreEvals = getxScoreDropByEval(dfGM)
    plotBarChart(xScoreEvals, 'Evaluation', 'Relative number of mistakes', 'Mistakes depending on evaluation in chess 960', width=10, limits=[-350, 550], filename='../out/evalMistakes.png')
    xScore = getxScoreDrops(dfGM)
    plotBarChart(xScore, 'Expected score drop', 'Relative number of moves', 'Distribution of expected score loss', isList=False, limits=[-0.5, 52], y_log=True, filename='../out/chess960Acc.png')
    # cDF = pd.read_pickle('../out/gameDF')
    # cGMDF = filterGamesByRating(cDF, (2500, 2900), 150, True)
    # xScore2 = getxScoreDrops(cGMDF)
    # plotBarChart(xScore2, 'Expected score drop', 'Relative number of moves', 'Distribution of expected score loss', isList=False, data2=xScore, limits=[-0.5, 52], y_log=True)
    # plotBarChart(xScore, 'Expected score drop', 'Relative number of moves', 'Distribution of expected score loss', isList=False, limits=[-0.5, 52], y_log=True, filename='../out/normalAcc.png')
    # df27 = filterGamesByRating(df, (2700, 2900), 100)
    """
    """
    points = list()
    for cp in [50, 100, 150, 200, 250, 300, 500]:
        prob = getExpectedScore(dfGM, cp)
        print(prob)
        points.append((cp, prob*100))
    plotExpectedScore(points, [(winPLichess, 0.00368208)], ["Lichess win probability"], "Lichess win percentage compared to GM score", filename='../out/lichessWinp.png')
    plotExpectedScore(points, [(winPLichess, 0.00368208), (winPLichess, 0.007545)], ["Lichess win probability", "k=0.007545"], "Updated expected score compared to GM score", filename='../out/newK.png')
    plotExpectedScore(points, [(winPLichess, 0.00368208), (winPLichess, 0.007545), (expectedScore, 0.007851)], ["Lichess win probability", "k=0.007545", "arctan"], "arctan approximation compared to GM score", filename='../out/arctan.png')
    """
    """
    drops = getExpectedScoreDrop(dfGM, (expectedScore, 0.007851), 0)
    # dropsM10 = getExpectedScoreDrop(dfGM, (expectedScore, 0.007851), 15)
    cDrops = getCumulativeDrop(drops)
    gameDrops = getGameExpectedScoreDrops(dfGM, (expectedScore, 0.007851))
    cGameDrops = getCumulativeDrop(gameDrops)
    dfDraws = dfGM[dfGM["Result"] == "1/2-1/2"]
    dDrops = getCumulativeDrop(getGameExpectedScoreDrops(dfDraws, (expectedScore, 0.007851)))
    dfDecisive = dfGM[(dfGM["Result"] == "1-0") | (dfGM["Result"] == "0-1")]
    decisive = getCumulativeDrop(getGameExpectedScoreDrops(dfDecisive, (expectedScore, 0.007851)))
    # plotAccuracies([cDrops], ["Expected score loss"], 'Move Accuracy', ('Expected score loss', 'Percentage of moves'), filename='../out/moveAccuracy.png')
    plotAccuracies([cGameDrops], ["CDF of AXSL"], 'Fitting a cuve to the AXSL', ("Average expected score loss per move", "Percentile of games"), filename='../out/fittedCurveAXSL.png')
    # plotAccuracies([cGameDrops, dDrops, decisive], ["All games", "Draws", "Decisive games"], 'AXSL for different game results', ('Average expected score loss per move', 'Percentile of games'), filename='../out/gameResultAXSL.png')
    """
    """
    moveData = [cGameDrops]
    moveNumbers = [0, 30, 40, 55, 10000]
    for i, minMove in enumerate(moveNumbers):
        if i < len(moveNumbers)-1:
            maxMove = moveNumbers[i+1]
        else:
            break
        dfMoves = filterDataByGameMoves(dfGM, minMove, maxMove)
        print(len(dfMoves))
        moveData.append(getCumulativeDrop(getGameExpectedScoreDrops(dfMoves, (expectedScore, 0.007851))))
    plotAccuracies(moveData, ["All games", "0-30", "30-40", "40-55", "55+"], 'AXSL for different game lengths', ('Average expected score loss per move', 'Percentile of games'), filename='../out/lengthAXSL.png')
    """
    # plotAccuracyDistribution(gameDrops, filename='../out/axsDistribution.png')
