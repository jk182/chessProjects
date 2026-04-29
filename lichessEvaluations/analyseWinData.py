import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper


def getWinsByCP(data: pd.DataFrame, timeControl: str, maxRatingDiff: int = 100, minRemainingTime: int = 60, cpBandWidth: int = 20, minCP: int = 0, maxCP: int = 2000) -> dict:
    cpData = dict()
    cpBands = [i for i in range(minCP, maxCP+cpBandWidth, cpBandWidth)]
    for b in cpBands:
        cpData[b] = [0, 0]
    for i, row in data.iterrows():
        if timeControl != row["TimeControl"]:
            continue
        if abs(row["WhiteElo"]-row["BlackElo"]) > maxRatingDiff:
            continue
        if row["WhiteTimeLeft"] < minRemainingTime:
            continue
        if row["FirstEvalAdvantage"] < 0:
            continue

        if row["Result"] == '1-0':
            wScore = 1
        elif row["Result"] == '1/2-1/2':
            wScore = 0.5
        else:
            wScore = 0

        bandNr = (row["FirstEvalAdvantage"] - minCP) // cpBandWidth

        index = min(minCP + bandNr * cpBandWidth, maxCP)
        cpData[index][0] += wScore
        cpData[index][1] += 1

    for k, v in cpData.items():
        print(k, v[0]/v[1])

    return cpData


def getHeatmapData(df: pd.DataFrame, timeGroupWidth: int = 1, maxTime: int = 180, cpGroupWidth: int = 10, maxCP: int = 1000, discardHigherCPs: bool = False) -> list:
    baseData = [[[0, 0] for _ in range(maxTime // timeGroupWidth + 1)] for _ in range(maxCP // cpGroupWidth + 1)]

    for i, row in df.iterrows():
        if discardHigherCPs and abs(row["Evaluation"]) > maxCP:
            continue

        if row["Result"] == '1-0':
            score = 1
        elif row["Result"] == '1/2-1/2':
            score = 0.5
        else:
            score = 0
        
        if row['Evaluation'] < 0:
            score = 1 - score
            timeLeft = row['BlackTimeLeft']
        else:
            timeLeft = row['WhiteTimeLeft']

        cpIndex = int((min(abs(row['Evaluation']), maxCP) + cpGroupWidth/2) // cpGroupWidth)
        timeIndex = int((min(maxTime, timeLeft) + timeGroupWidth/2) // timeGroupWidth)

        baseData[cpIndex][timeIndex][0] += score
        baseData[cpIndex][timeIndex][1] += 1

    data = list()
    for i in range(len(baseData)):
        data.append(list())
        for j in range(len(baseData[i])):
            if baseData[i][j][1] > 0:
                data[i].append(baseData[i][j][0] / baseData[i][j][1])
            else:
                data[i].append(-1)
    return data


def plotTimeEvaluationHeatmap(data: pd.DataFrame, timeControl: str, maxRatingDiff: int = 100, cpBandWidth: int = 10, timeBandWidth: int = 1, maxCP: int = 1000, maxTime: int = None):
    tcDF = df[df['TimeControl'] == timeControl]
    tcDF = tcDF[(tcDF['Ply'] == 30) | (tcDF['Ply'] == 40) | (tcDF['Ply'] == 50) | (tcDF['Ply'] == 60) | (tcDF['Ply'] == 70)]

    nSamples = 256
    colorMap = mpl.colormaps['plasma'].resampled(nSamples)
    newColors = colorMap(np.linspace(0, 1, nSamples))
    newColors[0] = [0, 0, 0, 1]
    colorMap = ListedColormap(newColors)
    
    fig, axs = plt.subplots(3, 3, figsize=(6, 8))
    for i, rating in enumerate([1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]):
        if rating < 2600:
            nDF = tcDF[(abs(tcDF['WhiteElo'] - rating) <= 100) & (abs(tcDF['BlackElo'] - rating) <= 100) & (abs(tcDF['WhiteElo'] - tcDF['BlackElo']) <= 50)]
        else:
            nDF = tcDF[(tcDF['WhiteElo'] >= rating-50) & (tcDF['BlackElo'] >= rating-50) & (abs(tcDF['WhiteElo'] - tcDF['BlackElo']) <= 150)]
        plotData = getHeatmapData(nDF, timeBandWidth, maxTime, cpBandWidth, maxCP, discardHigherCPs=True)
        alpha = np.reshape([0 if plotData[i][j] == -1 else 1 for i in range(len(plotData)) for j in range(len(plotData[i]))], shape=(len(plotData), len(plotData[0])))
        cAX = axs[i//3][i%3]
        im = cAX.imshow(plotData, cmap=colorMap, interpolation='bicubic', vmin=0.4, vmax=1)
        cAX.figure.colorbar(im)
        cAX.set_title(rating)

    fig.tight_layout()
    plt.show()


def getScoresByEvalFromDataFrame(df: pd.DataFrame, maxCP: int = 1000, cpGroupWidth: int = 20, discardHigherCPs: bool = False, whitePerspective: bool = True) -> dict:
    """
    A helper function to extract the score for each evaluation from the dataframe
    df: pd.DataFrame
        Dataframe containing the data from Lichess games
    maxCP: int
        The maximum (and negative of the minimum) evaluation to be considered
    cpGroupWidth: int
        The group width for the evaluation
    discardHigherCPs: bools
        If this is set, higher evaluations than the maximum will simply be ignored
    whitePerspective: bool
        If this is set, all evaluations and results are from white's perspective.
        Otherwise, everything is taken from the perspective of the side with the advantage
    """
    data = dict()
    if whitePerspective:
        for i in range(-maxCP, maxCP+cpGroupWidth, cpGroupWidth):
            data[i] = [0, 0]
    else:
        for i in range(0, maxCP+cpGroupWidth, cpGroupWidth):
            data[i] = [0, 0]

    for i, row in df.iterrows():
        if discardHigherCPs and abs(row["Evaluation"]) > maxCP:
            continue
        if row["Result"] == '1-0':
            score = 1
        elif row["Result"] == '1/2-1/2':
            score = 0.5
        else:
            score = 0

        cpIndex = cpGroupWidth * ((min(maxCP, abs(row["Evaluation"])) + cpGroupWidth/2) // cpGroupWidth)
        if row["Evaluation"] < 0:
            cpIndex *= -1
        
        if not whitePerspective and cpIndex < 0:
            cpIndex *= -1
            score = 1 - score

        data[cpIndex][0] += score
        data[cpIndex][1] += 1

    return {k: (v[0]/v[1] if v[1] != 0 else 0) for k, v in data.items()}


def plotScoreAndEval(df: pd.DataFrame, maxCP: int = 1000, cpBandWidth: int = 20, whitePerspective: bool = True):
    df = df[(df['WhiteElo'] > 2000) & (df['BlackElo'] > 2000)]
    fig, axs = plt.subplots(3, 2, figsize=(10, 6))
    for i, ply in enumerate([30, 40, 50, 60, 70, 80]):
        nDF = df[df['Ply'] == ply]
        plotData = getScoresByEvalFromDataFrame(nDF, maxCP, cpBandWidth, whitePerspective=whitePerspective)
        xVals = list(plotData.keys())
        yVals = list(plotData.values())

        cAX = axs[i//2][i%2]
        # axs[i//2][i%2].plot(xVals, yVals)
        cAX.plot(xVals, yVals)
        x = np.linspace(-maxCP, maxCP)
        y = (x+maxCP)/(maxCP*2)
        cAX.plot(x, y, zorder=-1)
        cAX.set_title(f'Ply {ply}')
        cAX.set_facecolor(plotting_helper.getColor('background'))
        cAX.hlines(0.5, -maxCP, maxCP, color='black', linewidth=0.5, zorder=-1)
        cAX.vlines(0, 0, 1, color='black', linewidth=0.5, zorder=-1)
        if whitePerspective:
            cAX.set_xlim(-maxCP, maxCP)
            cAX.set_ylim(-0.01, 1.01)
        else:
            cAX.set_xlim(0, maxCP)
            cAX.set_ylim(0.5, 1.01)
    plt.show()



if __name__ == '__main__':
    dataPath = '../out/lichessEvaluationsPlys2.pkl'
    dataPath = '../out/lichessEvaluationsPlys.pkl'
    allPath = '../out/lichessEvaluations2025-10.pkl'
    # df = pd.read_pickle(dataPath)
    df1 = pd.read_pickle(allPath)
    df2 = pd.read_pickle('../out/lichessEvaluations2025-09.pkl')
    df3 = pd.read_pickle('../out/lichessEvaluations2025-09_2.pkl')
    df = pd.concat([df1, df2, df3])
    # getWinsByCP(df, '180+0')
    plotTimeEvaluationHeatmap(df, '180+0', timeBandWidth=3, maxTime=171, maxCP=750, cpBandWidth=10)
    # plotTimeEvaluationHeatmap(df, '300+0', timeBandWidth=3, maxTime=300, maxCP=1000, cpBandWidth=10)
    # tcDF = df[df['TimeControl'] == '180+0']
    # plotScoreAndEval(tcDF, cpBandWidth=10, maxCP=750, whitePerspective=False)
