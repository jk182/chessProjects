import chess
import chess.pgn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotting_helper


def extractResultData(pgnPath: str) -> pd.DataFrame:
    keys = ['White', 'Black', 'WhiteElo', 'BlackElo', 'Date', 'Event', 'Result']
    data = dict()
    for key in keys:
        data[key] = list()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            for key in keys:
                if key in game.headers.keys():
                    if 'Elo' in key:
                        data[key].append(int(game.headers[key]))
                    else:
                        data[key].append(game.headers[key])
                else:
                    data[key].append(None)

    df = pd.DataFrame(data)
    return df


def getResultsByRating(df: pd.DataFrame, rating: int, white: bool, offset: int = 10, oppRatingGroupWidth: int = 0) -> dict:
    """
    This function gets the result for the given rating against all other ratings
    df: pd.DataFrame
        The data extracted by extractResultData
    rating: int
        The rating of the players to look at
    white: bool
        If the games are from White's or Black's perspective
    offset: int
        Offset for a range of ratings
    """
    data = dict()
    if white:
        color = 'White'
        oppColor = 'Black'
    else:
        color = 'Black'
        oppColor = 'White'
    
    for i, row in df.iterrows():
        if row['WhiteElo'] is None or row['BlackElo'] is None:
            continue
        if rating-offset <= row[f'{color}Elo'] <= rating+offset:
            r = row['Result']
            if r == '1-0':
                rIndex = 0
            elif r == '1/2-1/2':
                rIndex = 1
            elif r == '0-1':
                rIndex = 2
            else:
                continue
            if not white:
                rIndex = 2-rIndex

            oppElo = row[f'{oppColor}Elo']
            if oppElo in data:
                data[oppElo][rIndex] += 1
                data[oppElo][3] += 1
            else:
                data[oppElo] = [0, 0, 0, 1]
                data[oppElo][rIndex] += 1

    if oppRatingGroupWidth > 0:
        minRating = int(min(data.keys()))
        minRating -= minRating%oppRatingGroupWidth
        ratingGroups = [r for r in range(minRating, int(max(data.keys()))+oppRatingGroupWidth, oppRatingGroupWidth)]
        groupedData = dict()
        for k, v in data.items():
            for i in range(len(ratingGroups)):
                if ratingGroups[i]-oppRatingGroupWidth/2 <= k < ratingGroups[i]+oppRatingGroupWidth/2:
                    r = ratingGroups[i]
                    break
            if r in groupedData:
                for i in range(len(v)):
                    groupedData[r][i] += v[i]
            else:
                groupedData[r] = v

        data = groupedData

    avgData = dict()
    for k, v in data.items():
        avgData[k] = [round(v[i]/v[3], 3) for i in range(3)]
    return dict(sorted(avgData.items()))


def getDataPoints(data: pd.DataFrame, ratings: list, oppGroups: int):
    wDataPoints = dict()
    bDataPoints = dict()
    for rating in ratings:
        wData = getResultsByRating(data, rating, True, oppRatingGroupWidth=oppGroups)
        for k, v in wData.items():
            rDiff = rating - k
            if rDiff not in wDataPoints:
                wDataPoints[rDiff] = list()
            wDataPoints[rDiff].append(v)

        bData = getResultsByRating(data, rating, False, oppRatingGroupWidth=oppGroups)
        for k, v in bData.items():
            rDiff = rating - k
            if rDiff not in bDataPoints:
                bDataPoints[rDiff] = list()
            bDataPoints[rDiff].append(v)
    return [wDataPoints, bDataPoints]


def plotResultData(data: dict, filename: str = None):
    plotData = dict()
    for k, v in data.items():
        plotData[k] = v[0] + 0.5*v[1]

    plotting_helper.plotScatterPlot([list(plotData.keys())], [list(plotData.values())], 'Opponent rating', 'Score', 'Score for 2700 players depending on opponent rating', refFunction=eloFormula2, filename=filename)


def eloFormula(playerRating: int, oppRating: int) -> float:
    return 1 / (1 + 10**((oppRating-playerRating)/400))
    

def eloFormula2(oppRating: int, rating: int = 2700) -> float:
    return 1 / (1 + 10**((oppRating-rating)/400))


def drawRate(oppRating: int) -> float:
    return 0.6
    

def plotResults(xValues: list, yValues: list, xLabel: str, yLabel: str, title: str, scatterColors: list = None, legend: list = None, rating: int = None, filename: str = None):
    if not scatterColors:
        scatterColors = plotting_helper.getDefaultColors()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(plotting_helper.getColor('background'))
    
    xMin = min(xValues[0])
    xMax = max(xValues[0])
    for i in range(len(xValues)):
        if legend:
            ax.scatter(xValues[i], yValues[i], color=scatterColors[i%len(scatterColors)], label=legend[i])
        else:
            ax.scatter(xValues[i], yValues[i], color=scatterColors[i%len(scatterColors)])
        xMin = min(xMin, min(xValues[i]))
        xMax = max(xMax, max(xValues[i]))

    if rating:
        steps = 100
        xVals = [xMin + i/steps*(xMax-xMin) for i in range(steps+1)]
        if legend:
            ax.plot(xVals, [eloFormula(rating, x) for x in xVals], label=legend[-1])
            # ax.plot(xVals, [eloFormula(rating-40, x) for x in xVals], label='Elo formula black')
            ax.legend()
        else:
            ax.plot(xVals, [eloFormula(rating, x) for x in xVals])

    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    plt.title(title)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def drawRate(ratingDiff, a):
    return 3.2*np.exp(ratingDiff/a) / (1+np.exp(ratingDiff/a))**2 + 0.2


def plotDrawRates(xValues: list, yValues: list, xLabel: str, yLabel: str, title: str, scatterColors: list = None, legend: list = None, filename: str = None):
    """
    A general function to generate scatter plots
    """
    if not scatterColors:
        scatterColors = plotting_helper.getDefaultColors()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(plotting_helper.getColor('background'))
    
    xMin = min(xValues[0])
    xMax = max(xValues[0])
    for i in range(len(xValues)):
        if legend:
            ax.scatter(xValues[i], yValues[i], color=scatterColors[i%len(scatterColors)], label=legend[i])
        else:
            ax.scatter(xValues[i], yValues[i], color=scatterColors[i%len(scatterColors)])
        xMin = min(xMin, min(xValues[i]))
        xMax = max(xMax, max(xValues[i]))

    steps = 500
    xVals = [i/steps*(300) for i in range(steps+1)]
    ax.plot(xVals, [drawRate(x, 96.3816) for x in xVals], label='White draw rate formula')
    ax.plot(xVals, [drawRate(x, 160.82) for x in xVals], label='Black draw rate formula')

    if legend:
        ax.legend()

    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    plt.title(title)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()

if __name__ == '__main__':
    pgn = '../resources/2500+gamesUTF8.pgn'
    # df = extractResultData(pgn)
    # print(df)
    # df.to_pickle('../out/all2500games.pkl')
    df = pd.read_pickle('../out/all2500games.pkl')
    white = getResultsByRating(df, 2750, True, oppRatingGroupWidth=50)
    black = getResultsByRating(df, 2750, False, oppRatingGroupWidth=50)
    # plotResultData(white)
    # plotResultData(black)
    # dp = getDataPoints(df, [2500, 2550, 2600, 2650, 2700, 2750, 2800, 2850], 20)

    # Draws
    ratings = [250, 200, 150, 100, 50]
    wDrawRates = [0.45, 0.51, 0.65, 0.79, 0.92]
    bDrawRates = [0.63, 0.76, 0.87, 0.98, 0.98]
    plotDrawRates([ratings, ratings], [wDrawRates, bDrawRates], 'Rating advantage', 'Relative number of draws', 'Relative number of draws based on rating advantage', plotting_helper.getColors(['orange', 'black']), ['White draws', 'Black draws'])

    """
    dp = getDataPoints(df, [2700, 2750, 2800], 20)
    wDP = dp[0]
    bDP = dp[1]
    drawData = list()
    for rDiff, wdls in wDP.items():
        for wdl in wdls:
            drawData.append((rDiff, wdl[1]))

    bDrawData = list()
    for rDiff, wdls in bDP.items():
        for wdl in wdls:
            bDrawData.append((rDiff, wdl[1]))
    
    linReg = np.poly1d(np.polyfit([d[0] for d in drawData], [d[1] for d in drawData], 1))
    bLinReg = np.poly1d(np.polyfit([d[0] for d in bDrawData], [d[1] for d in bDrawData], 1))
    cubeReg = np.poly1d(np.polyfit([d[0] for d in drawData], [d[1] for d in drawData], 3))

    myline = np.linspace(-150, 250, 5000)
    """

    for rating in [2700]:
        white = getResultsByRating(df, rating, True, oppRatingGroupWidth=20)
        black = getResultsByRating(df, rating, False, oppRatingGroupWidth=20)
        wPlot = dict()
        for k, v in white.items():
            wPlot[k] = v[0] + v[1]*0.5
        bPlot = dict()
        for k, v in black.items():
            bPlot[k] = v[0] + v[1]*0.5
        
        xValues = [list(wPlot.keys()), list(bPlot.keys())]
        yValues = [list(wPlot.values()), list(bPlot.values())]
        plotResults(xValues, yValues, 'Opponent rating', 'Score', f'Score for {rating} players with white and black against various ratings', rating=rating, scatterColors=plotting_helper.getColors(['orange', 'black']), legend=['Score with white', 'Score with black', 'Score by the Elo formula'], filename='../out/score2700.png')
        # plotting_helper.plotScatterPlot(xValues, yValues, 'Opponent rating', 'Score', f'Score for {rating} players with white and black against various ratings', scatterColors=plotting_helper.getColors(['orange', 'black']), legend=['Score with white', 'Score with black'])

    """
    white2500 = getResultsByRating(df, 2500, True, oppRatingGroupWidth=50)
    black2500 = getResultsByRating(df, 2500, False, oppRatingGroupWidth=50)
    white2600 = getResultsByRating(df, 2600, True, oppRatingGroupWidth=50)
    black2600 = getResultsByRating(df, 2600, False, oppRatingGroupWidth=50)
    white2650 = getResultsByRating(df, 2650, True, oppRatingGroupWidth=50)
    black2650 = getResultsByRating(df, 2650, False, oppRatingGroupWidth=50)
    white2700 = getResultsByRating(df, 2700, True, oppRatingGroupWidth=50)
    black2700 = getResultsByRating(df, 2700, False, oppRatingGroupWidth=50)
    # white2800 = getResultsByRating(df, 2850, True, offset=50, oppRatingGroupWidth=50)
    # black2800 = getResultsByRating(df, 2850, False, offset=50, oppRatingGroupWidth=50)
    white2800 = getResultsByRating(df, 2800, True, oppRatingGroupWidth=50)
    black2800 = getResultsByRating(df, 2800, False, oppRatingGroupWidth=50)
    wWins = [v[0] for v in white.values()]
    wDraws = [v[1] for v in white.values()]
    wLosses = [v[2] for v in white.values()]
    bWins = [v[0] for v in black.values()]
    bDraws = [v[1] for v in black.values()]
    bLosses = [v[2] for v in black.values()]
    wDraws2500 = [v[1] for v in white2500.values()]
    bDraws2500 = [v[1] for v in black2500.values()]
    wDraws2600 = [v[1] for v in white2600.values()]
    bDraws2600 = [v[1] for v in black2600.values()]
    wDraws2650 = [v[1] for v in white2650.values()]
    bDraws2650 = [v[1] for v in black2650.values()]
    wDraws2700 = [v[1] for v in white2700.values()]
    bDraws2700 = [v[1] for v in black2700.values()]
    wDraws2800 = [v[1] for v in white2800.values()]
    bDraws2800 = [v[1] for v in black2800.values()]
    print('2500')
    print(white2500.keys())
    print(wDraws2500)
    print(black2500.keys())
    print(bDraws2500)
    print('2600')
    print(white2600.keys())
    print(wDraws2600)
    print(black2600.keys())
    print(bDraws2600)
    print('2650')
    print(white2650.keys())
    print(wDraws2650)
    print(black2650.keys())
    print(bDraws2650)
    print('2700')
    print(white2700.keys())
    print(wDraws2700)
    print(black2700.keys())
    print(bDraws2700)
    print('2750')
    print(white.keys())
    print(wDraws)
    print(black.keys())
    print(bDraws)
    print('2800+')
    print(white2800.keys())
    print(wDraws2800)
    print(black2800.keys())
    print(bDraws2800)
    # plotting_helper.plotLineChart([white.keys(), white.keys(), white.keys(), black.keys(), black.keys(), black.keys()], [wWins, wDraws, wLosses, bWins, bDraws, bLosses], 'Opponent rating', 'Relative number of games', 'WDL by rating', ['White wins', 'White draws', 'White losses', 'Black wins', 'Black draws', 'Black losses', 'Draw rate formula'], colors=plotting_helper.getColors(['purple', 'yellow', 'lightred', 'violet', 'orange', 'red']), refFunction=linReg)
    plotting_helper.plotLineChart([white.keys(), black.keys(), white2700.keys(), black2700.keys(), white2800.keys(), black2800.keys()], [wDraws, bDraws, wDraws2700, bDraws2700, wDraws2800, bDraws2800], 'Opponent rating', 'Relative number of games', 'Draws', ['White 2750', 'Black 2750', 'White 2700', 'Black 2700', 'White 2800', 'Black 2800'], colors=plotting_helper.getColors(['purple', 'violet', 'yellow', 'orange', 'lightred', 'red']))
    """

    """
    plt.plot(myline, linReg(myline))
    plt.plot(myline, bLinReg(myline))
    plt.plot(myline, cubeReg(myline))
    plt.plot([2750-r for r in white.keys()], wDraws)
    plt.plot([2750-r for r in black.keys()], bDraws)
    plt.show()
    """
