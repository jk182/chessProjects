import chess
import chess.pgn
import polars as pl
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import numpy as np

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper

import pickle


def getEndgameType(board: chess.Board) -> str:
    """
    This function gets the type of endgame on the board
    Return categories:
    """
    fen = board.fen()
    whitePieces = list()
    blackPieces = list()
    for s in fen.split()[0]:
        if s in 'NBRQ':
            whitePieces.append(s)
        elif s in 'nbrq':
            blackPieces.append(s)
        
    return f'{"".join(sorted(whitePieces))}-{"".join(sorted(blackPieces))}'


def extractEndgameConversionRates(pgnPaths: list) -> pl.DataFrame:
    data = dict()
    keys = ['Timecontrol', 'WhiteElo', 'BlackElo', 'WhiteStartTime', 'BlackStartTime', 'EndgameType', 'Result', 'StartEval', 'EndEval', 'Flawless', 'StartPly', 'EndPly', 'GameOver']

    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        print(pgnPath)
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                wElo = game.headers["WhiteElo"]
                bElo = game.headers["BlackElo"]
                result = game.headers["Result"]
                tc = game.headers["TimeControl"]

                node = game
                lastEval = 20
                lastEndgameType = None
                flawless = True
                plySinceEndgameType = 0
                ply = 0
                gameOver = False
                whiteStartTime = None
                blackStartTime = None

                while not node.is_end():
                    node = node.variations[0]
                    if node.turn():
                        blackTime = node.clock()
                    else:
                        whiteTime = node.clock()
                    board = node.board()
                    ply += 1
                    if node.eval() is not None:
                        lastEval = node.eval().white().score(mate_score=10000)

                    if functions.getGamePhase(board) == 'endgame':
                        endgameType = getEndgameType(board)
                        if lastEndgameType is None:
                            lastEndgameType = endgameType
                            startEval = lastEval
                            startPly = ply
                            whiteStartTime = whiteTime
                            blackStartTime = blackTime
                        if endgameType == lastEndgameType:
                            plySinceEndgameType += 1
                            if lastEval * startEval < 0:
                                if abs(lastEval-startEval) > 100:
                                    flawless = False
                            else:
                                if abs(startEval) - abs(lastEval) > 100 and abs(lastEval) < 200:
                                    flawless = False
                        else:
                            if plySinceEndgameType >= 5:
                                data['Timecontrol'].append(tc)
                                data['WhiteElo'].append(wElo)
                                data['BlackElo'].append(bElo)
                                data['WhiteStartTime'].append(whiteStartTime)
                                data['BlackStartTime'].append(blackStartTime)
                                data['EndgameType'].append(lastEndgameType)
                                data['Result'].append(result)
                                data['StartEval'].append(startEval)
                                data['EndEval'].append(lastEval)
                                data['Flawless'].append(flawless)
                                data['StartPly'].append(startPly)
                                data['EndPly'].append(ply)
                                data['GameOver'].append(gameOver)

                            lastEndgameType = endgameType
                            plySinceEndgameType = 0
                            flawless = True
                            startPly = ply
                            whiteStartTime = whiteTime
                            blackStartTime = blackTime

                if plySinceEndgameType >= 5:
                    data['Timecontrol'].append(tc)
                    data['WhiteElo'].append(wElo)
                    data['BlackElo'].append(bElo)
                    data['WhiteStartTime'].append(whiteStartTime)
                    data['BlackStartTime'].append(blackStartTime)
                    data['EndgameType'].append(endgameType)
                    data['Result'].append(result)
                    data['StartEval'].append(startEval)
                    data['EndEval'].append(None)
                    data['Flawless'].append(flawless)
                    data['StartPly'].append(startPly)
                    data['EndPly'].append(ply)
                    data['GameOver'].append(gameOver)

    df = pl.DataFrame(data)
    return df


def analyseEndgameData(df: pl.DataFrame, timeControl: str = None):
    data = dict()
    ratings = [1200, 1400, 1600, 1800, 2000, 2200, 2400]
    for row in df.iter_rows(named=True):
        if timeControl:
            if row['Timecontrol'] != timeControl:
                continue

        if row['StartEval'] is None or row['EndEval'] is None:
            continue

        if row['StartEval'] > 0:
            elo = int(row['WhiteElo'])
            startTime = row['WhiteStartTime']
        else:
            elo = int(row['BlackElo'])
            startTime = row['BlackStartTime']

        if startTime < 15:
            continue

        endgameType = row['EndgameType']
        if endgameType.split('-')[0].lower() != endgameType.split('-')[1].lower():
            continue

        if endgameType not in data:
            data[endgameType] = dict()
            for rating in ratings:
                data[endgameType][rating] = list()

        evalIndex = abs(row['StartEval'])
        for rating in ratings:
            if abs(elo-rating) <= 100:
                ratingIndex = rating
                break

        """
        if (evalIndex, startTime) not in data[endgameType][ratingIndex]:
            # data[endgameType][ratingIndex][evalIndex] = [0, 0]
            data[endgameType][ratingIndex][(evalIndex, startTime)] = list()
        """

        if row['StartEval'] * row['EndEval'] > 0 and (abs(row['EndEval']) > 200 or abs(row['EndEval']) > abs(row['StartEval'])):
            # data[endgameType][ratingIndex][evalIndex][0] += 1
            data[endgameType][ratingIndex].append((evalIndex, startTime, True))
        else:
            data[endgameType][ratingIndex].append((evalIndex, startTime, False))

        # data[endgameType][ratingIndex][evalIndex][1] += 1

    """
    for ending, d in data.items():
        print(ending)
        for k, v in d.items():
            # print(k, sorted([(k, round(v[0]/v[1], 3)) for k,v in v.items() if v[1] > 0]))
            print(k, v)
    """

    return data


def getHeatmapData(data: dict, maxTime: int, timeGroupWidth: float = 3, evalGroupWidth: int = 10, maxEval: int = 700) -> list:
    """
    This gets the data from analyseEndgameData and transforms it to a 2D list
    """
    timeLength = int(maxTime / timeGroupWidth) + 1
    evalLength = int(maxEval / evalGroupWidth) + 1
    heatmapData = dict()
    for ending, eData in data.items():
        heatmapData[ending] = dict()
        for rating, d in eData.items():
            heatmapData[ending][rating] = [[[0, 0] for _ in range(evalLength)] for _ in range(timeLength)]
            for x in d:
                evalIndex = min(int(x[0] // evalGroupWidth), int(maxEval/evalGroupWidth))
                timeIndex = min(int(x[1] // timeGroupWidth), int(maxTime/timeGroupWidth))
                heatmapData[ending][rating][timeIndex][evalIndex][1] += 1
                if x[2]:
                    heatmapData[ending][rating][timeIndex][evalIndex][0] += 1

    return heatmapData


def plotConversionData(data: dict, endingType: str = '-'):
    nSamples = 11
    colorMap = mpl.colormaps['plasma'].resampled(nSamples)
    newColors = colorMap(np.linspace(0, 1, nSamples))
    newColors[0] = [0, 0, 0, 1]
    colorMap = ListedColormap(newColors)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plotting_helper.getDefaultColors()
    rating = 2000

    for i, (k, v) in enumerate(data[endingType].items()):
        if k != rating:
            continue
        plotData = [[v[i][j][0]/v[i][j][1] if v[i][j][1] > 0 else -0.1 for j in range(len(v[i]))] for i in range(len(v))]
        """
        converted = [(evaluation, time) for (evaluation, time, c) in v if evaluation < 9000 and c]
        notConv = [(evaluation, time) for (evaluation, time, c) in v if evaluation < 9000 and not c]
        ax.scatter([c[0] for c in converted], [c[1] for c in converted], label=k, color='green', alpha=0.2)
        ax.scatter([c[0] for c in notConv], [c[1] for c in notConv], label=k, color='red', alpha=0.2)
        """

    ax.set_xlabel('Evaluation')
    ax.set_ylabel('Time')
    im = ax.imshow(plotData, cmap=colorMap)
    fig.colorbar(im, label='Game score') # , ax=axs, shrink=0.8, anchor=(1, 0.5))
    # ax.legend()
    plt.show()


def plotTimeConversion(data: dict):
    endings = ['R-r', 'Q-q', 'N-n', '-']
    tRating = 2000
    evalGroupWidth = 10
    plotData = list()
    for ending, eData in data.items():
        if ending not in endings:
            continue
        for rating, d in eData.items():
            if rating != tRating:
                continue
            data = dict()
            for x in d:
                evaluation = int(min(x[0], 500) / evalGroupWidth)
                if evaluation not in data:
                    data[evaluation] = [0, 0]

                data[evaluation][1] += 1
                if x[2]:
                    data[evaluation][0] += 1

            pd = dict()
            for k, v in data.items():
                pd[k] = v[0]/v[1]

            plotData.append(dict(sorted(pd.items())))

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, data in enumerate(plotData):
        ax.plot(data.keys(), data.values(), label=endings[i])

    ax.legend()
    plt.show()



if __name__ == '__main__':
    pgnFolder = '../out/lichessDB/'
    pgnPaths = [f'{pgnFolder}{p}' for p in os.listdir(pgnFolder) if 'endgame' in p]
    pgnPaths = ['../out/lichessDB/analysed_endgames_rating2000_180+0.pgn', '../out/lichessDB/analysed_endgames_rating2000_180+2.pgn']
    # pgnPaths = ['../out/testEnding.pgn']
    # outFile = '../out/endgameConversionData2.pkl'
    outFile = '../out/endgameConversionData2000_3+0-3+2.pkl'
    #  outFile = '../out/endgameConversionData180+2.pkl'
    """
    df = extractEndgameConversionRates(pgnPaths)
    with open(outFile, 'wb+') as f:
        pickle.dump(df, f)
    """

    with open(outFile, 'rb') as f:
        df = pickle.load(f)
    data = analyseEndgameData(df, timeControl='180+0')
    # plotTimeConversion(data)
    heatmapData = getHeatmapData(data, 180, timeGroupWidth=3, evalGroupWidth=10)
    plotConversionData(heatmapData, endingType='-')
