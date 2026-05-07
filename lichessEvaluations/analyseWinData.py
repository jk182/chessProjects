import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper
import functions


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
        elif row["Result"] == '0-1':
            score = 0
        else:
            continue
        
        if row['Evaluation'] < 0:
            score = 1 - score
            timeLeft = row['BlackTimeLeft']
        else:
            timeLeft = row['WhiteTimeLeft']

        # if timeLeft < 10 and abs(row['WhiteTimeLeft']-row['BlackTimeLeft']) > 50:
        if abs(row['WhiteTimeLeft']-row['BlackTimeLeft']) > timeLeft+min(2, timeLeft):
            continue

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


def plotTimeEvaluationHeatmap(data: pd.DataFrame, timeControl: str, maxRatingDiff: int = 100, cpBandWidth: int = 10, timeBandWidth: int = 1, maxCP: int = 1000, maxTime: int = None, filename: str = None):
    tcDF = df[df['TimeControl'] == timeControl]
    # tcDF = tcDF[(tcDF['Ply'] == 30) | (tcDF['Ply'] == 40) | (tcDF['Ply'] == 50) | (tcDF['Ply'] == 60) | (tcDF['Ply'] == 70)]
    if maxTime is None:
        maxTime = int(timeControl.split('+')[0])

    nSamples = 6
    colorMap = mpl.colormaps['plasma'].resampled(nSamples)
    newColors = colorMap(np.linspace(0, 1, nSamples))
    newColors[0] = [0, 0, 0, 1]
    colorMap = ListedColormap(newColors)
    ratings = [1500, 1800, 2100, 2400]

    nTicks = 5
    nXTicks = 6
    xTicks = [i*maxTime//(timeBandWidth*nXTicks) for i in range(nXTicks+1)]
    xTickLabels = [i*maxTime//nXTicks for i in range(nXTicks+1)]
    yTicks = [i*maxCP//(cpBandWidth*nTicks) for i in range(nTicks+1)]
    yTickLabels = [f'+{(i*maxCP//nTicks)/100}' for i in range(nTicks+1)]
    
    fig, axs = plt.subplots(2, 2, figsize=(8, 6))
    for i, rating in enumerate(ratings):
        cAX = axs[i//2][i%2]
        if i < len(ratings)-1:
            midRating = (rating+ratings[i+1])/2
            midDiff = (ratings[i+1]-rating) / 2
            nDF = tcDF[(abs(tcDF['WhiteElo'] - midRating) <= midDiff) & (abs(tcDF['BlackElo'] - midRating) <= midDiff) & (abs(tcDF['WhiteElo'] - tcDF['BlackElo']) <= 100)]
            cAX.set_title(f'{rating}-{ratings[i+1]} rated')
        else:
            nDF = tcDF[(tcDF['WhiteElo'] >= rating) & (tcDF['BlackElo'] >= rating) & (abs(tcDF['WhiteElo'] - tcDF['BlackElo']) <= 150)]
            cAX.set_title(f'{rating}+ rated')

        plotData = getHeatmapData(nDF, timeBandWidth, maxTime, cpBandWidth, maxCP, discardHigherCPs=True)
        im = cAX.imshow(plotData, cmap=colorMap, interpolation='bicubic', vmin=0.4, vmax=1, aspect=0.8)
        if i % 2 == 1:
            cBarLabel = 'Game score'
        else:
            cAX.set_ylabel('Evaluation')
            cBarLabel = ''
        # cAX.figure.colorbar(im, shrink=0.8, label=cBarLabel)
        cAX.set_xticks(xTicks, labels=xTickLabels)
        cAX.set_yticks(yTicks, labels=yTickLabels)
        cAX.set_xlabel('Time left in seconds')

    fig.colorbar(im, label='Game score', ax=axs, shrink=0.8, anchor=(1, 0.5))
    fig.suptitle('Score for a given evaluation and time left for different ratings', size=14)
    # fig.tight_layout()
    fig.patch.set_facecolor(plotting_helper.getColor('background'))
    fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.85)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
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
        elif row["Result"] == '0-1':
            score = 0
        else:
            continue

        cpIndex = cpGroupWidth * ((min(maxCP, abs(row["Evaluation"])) + cpGroupWidth/2) // cpGroupWidth)
        if row["Evaluation"] < 0:
            cpIndex *= -1
        
        if not whitePerspective and cpIndex < 0:
            cpIndex *= -1
            score = 1 - score

        data[cpIndex][0] += score
        data[cpIndex][1] += 1

    return {k: (v[0]/v[1] if v[1] != 0 else 0) for k, v in data.items()}


def getScoreByTimeAdvantageFromDataFrame(df: pd.DataFrame, timeAdvGroupWidth: int = 5) -> dict:
    data = dict()

    for i, row in df.iterrows():
        timeDiff = row['WhiteTimeLeft'] - row['BlackTimeLeft']
        if abs(timeDiff) > 180:
            continue
        timeAdv = abs(timeDiff) // timeAdvGroupWidth

        if row["Result"] == '1-0':
            score = 1
        elif row["Result"] == '1/2-1/2':
            score = 0.5
        elif row["Result"] == '0-1':
            score = 0
        else:
            continue

        if timeDiff < 0:
            score = 1 - score

        if timeAdv not in data:
            data[timeAdv] = [score, 1]
        else:
            data[timeAdv][0] += score
            data[timeAdv][1] += 1

    retData = dict(sorted({k*timeAdvGroupWidth: (v[0]/v[1] if v[1] > 0 else 0) for k, v in data.items()}.items()))
    return retData


def plotScoreAndEval(df: pd.DataFrame, maxCP: int = 1000, cpBandWidth: int = 20, whitePerspective: bool = True, filename: str = None):
    fig, axs = plt.subplots(3, 2, figsize=(10, 6))
    times = [20, 40, 60, 90, 120, 180]
    # times = [5, 10, 15, 20, 25, 30]
    ratings = [1400, 1800, 2200, 2600]
    colors = plotting_helper.getDefaultColors()

    for i, timeLeft in enumerate(times):
        cAX = axs[i//2][i%2]
        if i == 0:
            lastTime = 0
        else:
            lastTime = times[i-1]

        for j, rating in enumerate(ratings):
            if j < len(ratings)-1:
                midRating = (rating+ratings[j+1])/2
                midDiff = (ratings[j+1]-rating) / 2
                rDF = df[(abs(df['WhiteElo'] - midRating) <= midDiff) & (abs(df['BlackElo'] - midRating) <= midDiff) & (abs(df['WhiteElo'] - df['BlackElo']) <= 100)]
                label = f'{rating}-{ratings[j+1]}'
            else:
                rDF = df[(df['WhiteElo'] >= rating) & (df['BlackElo'] >= rating) & (abs(df['WhiteElo'] - df['BlackElo']) <= 150)]
                label = f'{rating}+'
            
            if whitePerspective:
                # nDF = rDF[(rDF['WhiteTimeLeft'] > lastTime) & (rDF['WhiteTimeLeft'] <= timeLeft)]
                nDF = rDF[(rDF['WhiteTimeLeft'] > lastTime) & (rDF['WhiteTimeLeft'] <= timeLeft) & (rDF['BlackTimeLeft'] > lastTime) & (rDF['BlackTimeLeft'] <= timeLeft)]
            else:
                nDF = rDF[((rDF['Evaluation'] >= 0) & (rDF['WhiteTimeLeft'] > lastTime) & (rDF['WhiteTimeLeft'] <= timeLeft)) | ((rDF['Evaluation'] < 0) & (rDF['BlackTimeLeft'] > lastTime) & (rDF['BlackTimeLeft'] <= timeLeft))]
            plotData = getScoresByEvalFromDataFrame(nDF, maxCP, cpBandWidth, whitePerspective=whitePerspective)
            xVals = list(plotData.keys())
            yVals = list(plotData.values())

            cAX.plot(xVals, yVals, color=colors[j%len(colors)], label=label)

        x = np.linspace(-maxCP, maxCP)
        y = (x+maxCP)/(maxCP*2)
        cAX.plot(x, y, zorder=-1)
        cAX.set_title(f'{lastTime}-{timeLeft}')
        cAX.set_facecolor(plotting_helper.getColor('background'))
        cAX.hlines(0.5, -maxCP, maxCP, color='black', linewidth=0.5, zorder=-1)
        cAX.vlines(0, 0, 1, color='black', linewidth=0.5, zorder=-1)
        cAX.legend()
        if whitePerspective:
            cAX.set_xlim(-maxCP, maxCP)
            cAX.set_ylim(-0.01, 1.01)
        else:
            cAX.set_xlim(0, maxCP)
            cAX.set_ylim(0.5, 1.01)

    fig.tight_layout()
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotScoresByRatings(df: pd.DataFrame, ratings: list, cpGroupWidth: int = 20, maxCP: int = 1000, nCols: int = 2, singlePlot: bool = True, filename: str = None):
    if singlePlot:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig, axs = plt.subplots(len(ratings)//nCols, nCols, figsize=(10, 6))

    # colors = plotting_helper.getDefaultColors()
    colors = plotting_helper.getColors(['grey', 'purple', 'blue', 'green', 'orange', 'red'])

    for i, rating in enumerate(ratings):
        if i < len(ratings)-1:
            midRating = (rating+ratings[i+1])/2
            midDiff = (ratings[i+1]-rating) / 2 - 50
            nDF = df[(abs(df['WhiteElo'] - midRating) <= midDiff) & (abs(df['BlackElo'] - midRating) <= midDiff) & (abs(df['WhiteElo'] - df['BlackElo']) <= 100)]
            label = f'{rating}-{ratings[i+1]}'
        else:
            nDF = df[(df['WhiteElo'] >= rating) & (df['BlackElo'] >= rating) & (abs(df['WhiteElo'] - df['BlackElo']) <= 150)]
            label = f'{rating}+'

        plotData = getScoresByEvalFromDataFrame(nDF, maxCP, cpGroupWidth)
        xVals = list(plotData.keys())
        yVals = list(plotData.values())

        if singlePlot:
            ax.plot(xVals, yVals, color=colors[(i+1)%len(colors)], label=label, linewidth=2)
        else:
            cAX = axs[i//nCols][i%nCols]
            cAX.plot(xVals, yVals, color=plotting_helper.getColor('blue'), label='Actual score')
            functionxVals = np.linspace(-maxCP, maxCP, 2048)
            cAX.plot(functionxVals, [functions.winP(x)/100 for x in functionxVals], color=plotting_helper.getColor('orange'), zorder=-1, label='Lichess expected score')
            cAX.set_facecolor(plotting_helper.getColor('background'))
            cAX.hlines(0.5, -maxCP, maxCP, color='black', linewidth=0.5, zorder=-1)
            cAX.vlines(0, 0, 1, color='black', linewidth=0.5, zorder=-1)
            cAX.set_xlim(-maxCP, maxCP)
            cAX.set_ylim(0, 1)
            cAX.set_xlabel('Evaluation')
            cAX.set_ylabel('White score')
            cAX.set_title(label)
            cAX.legend()

    if singlePlot:
        functionxVals = np.linspace(-maxCP, maxCP, 2048)
        ax.plot(functionxVals, [functions.winP(x)/100 for x in functionxVals], color=colors[0], zorder=-1, label='Lichess expected score')
        ax.set_facecolor(plotting_helper.getColor('background'))

        ax.set_xlabel('Evaluation')
        ax.set_ylabel('White score')
        ax.set_xlim(-maxCP, maxCP)
        ax.set_ylim(0, 1)
        xTickLabels = [f'+{int(label.get_text().replace('−', '-').replace('–', '-').replace('—', '-'))/100}' if int(label.get_text().replace('−', '-').replace('–', '-').replace('—', '-')) > 0 else f'{int(label.get_text().replace('−', '-').replace('–', '-').replace('—', '-'))/100}' for label in ax.get_xticklabels()]
        ax.set_xticklabels(xTickLabels)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        ax.grid()
        ax.legend()
        plt.title("White's score for a given evaluation at different rating levels in 3+0 games on Lichess")
        fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    else:
        fig.tight_layout()
        fig.suptitle('Lichess expected score compared to the actual score in 3+0 games based on evaluation')

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotScoreByTimeAdvantage(df: pd.DataFrame, timeAdvGroupWidth: int = 5):
    fig, axs = plt.subplots(3, 3, figsize=(10, 6))
    for i, rating in enumerate([1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]):
        if rating < 2600:
            nDF = df[(abs(df['WhiteElo'] - rating) <= 100) & (abs(df['BlackElo'] - rating) <= 100) & (abs(df['WhiteElo'] - df['BlackElo']) <= 100)]
        else:
            nDF = df[(df['WhiteElo'] >= rating-50) & (df['BlackElo'] >= rating-50) & (abs(df['WhiteElo'] - df['BlackElo']) <= 150)]

        plotData = getScoreByTimeAdvantageFromDataFrame(nDF, timeAdvGroupWidth)
        xVals = list(plotData.keys())
        yVals = list(plotData.values())

        cAX = axs[i//3][i%3]
        cAX.plot(xVals, yVals)
        cAX.set_title(rating)
        cAX.set_facecolor(plotting_helper.getColor('background'))
        cAX.set_xlim(0, 180)

    plt.show()


def plotEvalAndTimeAdvantage(df: pd.DataFrame, maxTimeAdvantage: int = 180, maxCP: int = 1000, filename: str = None):
    rating = 2200
    df = df[(abs(df['WhiteElo'] - rating) <= 100) & (abs(df['BlackElo'] - rating) <= 100) & (abs(df['WhiteElo'] - df['BlackElo']) <= 50)]
    xValues = list()
    yValues = list()
    for i, row in df.iterrows():
        timeAdv = row['WhiteTimeLeft']-row['BlackTimeLeft']
        if abs(timeAdv) > maxTimeAdvantage or abs(row['Evaluation']) > maxCP:
            continue
        xValues.append(timeAdv)
        yValues.append(row['Evaluation'])

    print(np.corrcoef(xValues, yValues))
    plotting_helper.plotScatterPlot([xValues], [yValues], 'White time advantage', 'Evaluation', 'Time advantage compared to evaluation')


def plotScoreByEvalAndTimeLeft(df: pd.DataFrame, rating: int, maxCP: int = 1000, cpGroupWidth: int = 25, timeLeft: list = [20, 40, 60, 80, 100, 120, 150, 180], showLichessWinP: bool = True, filename: str = None):
    colors = plotting_helper.getColors(['purple', 'blue', 'teal', 'yellow', 'darkorange', 'pink', 'much worse'])
    ratingOffset = 200
    df = df[(abs(df['WhiteElo'] - rating) <= ratingOffset) & (abs(df['BlackElo'] - rating) <= ratingOffset) & (abs(df['WhiteElo'] - df['BlackElo']) <= 50)]

    fig, ax = plt.subplots(figsize=(10, 6))

    plotData = getScoresByEvalFromDataFrame(df, maxCP, cpGroupWidth)
    xValues = list(plotData.keys())
    yValues = list(plotData.values())

    ax.plot(xValues, yValues, color=plotting_helper.getColor('grey'), label='Average expected score', linewidth=2)

    for i, time in enumerate(timeLeft):
        if i == 0:
            lastTime = 0
        else:
            lastTime = timeLeft[i-1]

        nDF = df[(df['WhiteTimeLeft'] > lastTime) & (df['WhiteTimeLeft'] <= time) & (df['BlackTimeLeft'] > lastTime) & (df['BlackTimeLeft'] <= time)]
        # nDF = df[(df['WhiteTimeLeft'] > lastTime) & (df['WhiteTimeLeft'] <= time) & (df['WhiteTimeLeft']-df['BlackTimeLeft'] < -20)]
        # nDF = df[(df['BlackTimeLeft'] > lastTime) & (df['BlackTimeLeft'] <= time)]
        plotData = getScoresByEvalFromDataFrame(nDF, maxCP, cpGroupWidth)
        xValues = list(plotData.keys())
        yValues = list(plotData.values())

        ax.plot(xValues, yValues, color=colors[i%len(colors)], label=f'{lastTime}-{time} seconds left', linewidth=2)

    if showLichessWinP:
        functionxVals = np.linspace(-maxCP, maxCP, 2048)
        ax.plot(functionxVals, [functions.winP(x)/100 for x in functionxVals], color=plotting_helper.getColor('grey'), zorder=-1, label='Lichess expected score')

    ax.legend()
    ax.set_facecolor(plotting_helper.getColor('background'))
    ax.set_xlim(-maxCP, maxCP)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Evaluation')
    ax.set_ylabel('White Score')
    xTickLabels = [f'+{int(label.get_text().replace('−', '-').replace('–', '-').replace('—', '-'))/100}' if int(label.get_text().replace('−', '-').replace('–', '-').replace('—', '-')) > 0 else f'{int(label.get_text().replace('−', '-').replace('–', '-').replace('—', '-'))/100}' for label in ax.get_xticklabels()]
    ax.set_xticklabels(xTickLabels)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
    ax.grid()
    plt.title(f"White's score for {rating} rated players in 3+0 with different amounts of time left")

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


if __name__ == '__main__':
    dataPath = '../out/lichessEvaluationsPlys2.pkl'
    dataPath = '../out/lichessEvaluationsPlys.pkl'
    allPath = '../out/lichessEvaluations2025-10.pkl'
    # df = pd.read_pickle(allPath)
    df1 = pd.read_pickle(allPath)
    df2 = pd.read_pickle('../out/lichessEvaluations2025-09.pkl')
    df3 = pd.read_pickle('../out/lichessEvaluations2025-09_2.pkl')
    df4 = pd.read_pickle('../out/lichessEvaluations2025-09_3.pkl')
    df5 = pd.read_pickle('../out/lichessEvaluations2025-09_4.pkl')
    df6 = pd.read_pickle('../out/lichessEvaluations2025-09_5.pkl')
    df7 = pd.read_pickle('../out/lichessEvaluations2025-02.pkl')
    df8 = pd.read_pickle('../out/lichessEvaluations2026-04.pkl')
    df = pd.concat([df1, df2, df3, df4, df5, df6, df7, df8])
    # print(df)
    # getWinsByCP(df, '180+0')
    # plotTimeEvaluationHeatmap(df, '60+0', timeBandWidth=1, maxTime=60, maxCP=750, cpBandWidth=10)
    # plotTimeEvaluationHeatmap(df, '180+0', timeBandWidth=3, maxTime=180, maxCP=1000, cpBandWidth=20, filename='../out/evalTimeHeatmap.png')
    # plotTimeEvaluationHeatmap(df, '180+0', timeBandWidth=1, maxTime=10, maxCP=750, cpBandWidth=25)
    # plotTimeEvaluationHeatmap(df, '180+2', timeBandWidth=3, maxTime=171, maxCP=750, cpBandWidth=10)
    tcDF = df[df['TimeControl'] == '180+0']
    # tcDF = tcDF[tcDF['Ply'] == 40]
    # tcDF = tcDF[(tcDF['Evaluation'] < 100) & (tcDF['Evaluation'] > -100)]
    plotScoreByEvalAndTimeLeft(tcDF, 1600, timeLeft=[10, 20, 30, 45, 60, 90, 180], cpGroupWidth=40, showLichessWinP=False, filename='../out/scoreByTime1600.png')
    plotScoreByEvalAndTimeLeft(tcDF, 2200, timeLeft=[5, 10, 20, 30, 45, 60, 180], cpGroupWidth=40, showLichessWinP=False, filename='../out/scoreByTime2200.png')
    # plotScoresByRatings(tcDF, [1400, 1700, 2000, 2300, 2600], maxCP=1000, cpGroupWidth=25, filename='../out/scoresByEvalBlitz.png')
    # plotScoreAndEval(tcDF, cpBandWidth=25, maxCP=750, whitePerspective=True)
    # plotScoreByTimeAdvantage(tcDF)
