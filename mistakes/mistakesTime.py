import chess
import pandas as pd
import numpy as np
import pickle
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper


def extractMoveData(pgnPaths: list) -> pd.DataFrame:
    mate_score = 100000
    data = dict()
    keys = ['Rating', 'TimeBefore', 'TimeAfter', 'EvalBefore', 'EvalAfter', 'MoveNr']
    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                elos = [int(game.headers['WhiteElo']), int(game.headers['BlackElo'])]

                times = [None, None]
                lastEval = None
                moveNr = 0

                node = game
                while not node.is_end():
                    color = node.board().turn
                    if color:
                        cIndex = 0
                        moveNr += 1
                    else:
                        cIndex = 1

                    if node.eval() is not None:
                        lastEval = int(node.eval().pov(color).score(mate_score=mate_score))
                    else:
                        lastEval = None

                    node = node.variations[0]
                    newTime = node.clock()
                    if node.eval() is not None:
                        newEval = int(node.eval().pov(color).score(mate_score=mate_score))
                    else:
                        newEval = None
                    if newTime is None and moveNr > 1:
                        # print('No Time')
                        newTime = times[cIndex]
                    if times[cIndex] is not None and lastEval is not None:
                        newTime = int(newTime)
                        data['Rating'].append(elos[cIndex])
                        data['TimeBefore'].append(int(times[cIndex]))
                        data['TimeAfter'].append(newTime)
                        data['EvalBefore'].append(lastEval)
                        data['EvalAfter'].append(newEval)
                        data['MoveNr'].append(moveNr)

                    times[cIndex] = newTime
                    
    df = pd.DataFrame(data)
    return df


def categoriseData(df: pd.DataFrame, timeIntervals: list, ratingGroups: list) -> list:
    imbCutoffs = [5, 10, 15]
    data = dict()
    ratingGroups = list(sorted(ratingGroups))
    timeIntervals = list(reversed(sorted(timeIntervals)))
    
    for r in ratingGroups:
        data[r] = dict()
        for t in timeIntervals:
            data[r][t] = [0, 0, 0, 0]

    for i, row in df.iterrows():
        if row['Rating'] < min(ratingGroups) or row['TimeBefore'] > max(timeIntervals):
            continue

        rating = max(ratingGroups)
        for j, r in enumerate(ratingGroups):
            if row['Rating'] < r:
                rating = ratingGroups[j-1]
                break

        time = min(timeIntervals)
        for j, t in enumerate(timeIntervals):
            if row['TimeBefore'] > t:
                time = timeIntervals[j-1]
                break

        xsDrop = functions.expectedScore(row['EvalBefore']) - functions.expectedScore(row['EvalAfter'])
        
        if xsDrop < imbCutoffs[0]:
            index = None
        elif imbCutoffs[0] <= xsDrop < imbCutoffs[1]:
            index = 0
        elif imbCutoffs[1] <= xsDrop < imbCutoffs[2]:
            index = 1
        else:
            index = 2

        data[rating][time][3] += 1
        if index is not None:
            data[rating][time][index] += 1
    return data


def getIMBdata(df: pd.DataFrame, timeIntervals: list, imbCutoffs: list = [5, 10, 15]) -> list:
    """
    This extracts the data of inaccuracies, mistakes and blunders depending on the time left and puts it into a format for plotting
    """
    data = dict()
    timeIntervals = list(reversed(sorted(timeIntervals)))

    for t in timeIntervals:
        data[t] = [0, 0, 0, 0]

    for i, row in df.iterrows():
        if row['TimeBefore'] > max(timeIntervals):
            continue

        time = min(timeIntervals)
        for j, t in enumerate(timeIntervals):
            if row['TimeBefore'] > t:
                time = timeIntervals[j-1]
                break
        
        xsDrop = functions.expectedScore(row['EvalBefore']) - functions.expectedScore(row['EvalAfter'])
        if imbCutoffs[0] <= xsDrop < imbCutoffs[1]:
            data[time][0] += 1
        elif imbCutoffs[1] <= xsDrop < imbCutoffs[2]:
            data[time][1] += 1
        elif imbCutoffs[2] <= xsDrop:
            data[time][2] += 1
        data[time][3] += 1

    plotData = [list(), list(), list()]
    for t, imb in data.items():
        for k in range(3):
            if imb[3] == 0:
                plotData[k].append(0)
            else:
                plotData[k].append(imb[k]/imb[3])
    return plotData


def getAccuracyData(df: pd.DataFrame, timeIntervals: list) -> list:
    """
    This calculates the accuracy at each time interval
    """
    data = dict()
    timeIntervals = list(reversed(sorted(timeIntervals)))

    for t in timeIntervals:
        data[t] = [0, 0]

    for i, row in df.iterrows():
        if row['TimeBefore'] > max(timeIntervals):
            continue

        time = min(timeIntervals)
        for j, t in enumerate(timeIntervals):
            if row['TimeBefore'] > t:
                time = timeIntervals[j-1]
                break
        
        accuracy = functions.accuracy(functions.expectedScore(row['EvalBefore']), functions.expectedScore(row['EvalAfter']))
        if np.isnan(accuracy):
            print('NAN')
            continue
        data[time][0] += accuracy
        data[time][1] += 1

    plotData = list()
    for k, v in data.items():
        if v[1] == 0:
            plotData.append(0)
        else:
            plotData.append(v[0]/v[1])
    return plotData


def mistakesWithTimeControl(df: pd.DataFrame, timeIntervals: list, mistakeCutoff: int = 10, tcMove: int = 40) -> list:
    data = dict()
    timeIntervals = list(reversed(sorted(timeIntervals)))

    for i in range(2):
        data[i] = dict()
        for t in timeIntervals:
            data[i][t] = [0, 0]

    for i, row in df.iterrows():
        if row['TimeBefore'] > max(timeIntervals):
            continue

        time = min(timeIntervals)
        for j, t in enumerate(timeIntervals):
            if row['TimeBefore'] > t:
                time = timeIntervals[j-1]
                break
        
        if row['MoveNr'] <= tcMove:
            index = 0
        else:
            index = 1
        xsDrop = functions.expectedScore(row['EvalBefore']) - functions.expectedScore(row['EvalAfter'])
        if xsDrop >= mistakeCutoff:
            data[index][time][0] += 1
        data[index][time][1] += 1
    
    plotData = [list(), list()]
    for i in range(2):
        for k, v in data[i].items():
            if v[1] == 0:
                plotData[i].append(0)
            else:
                plotData[i].append(v[0]/v[1])
    return plotData




def mistakesByTimeSpent(df: pd.DataFrame, timeIntervals: list) -> list:
    data = dict()
    timeIntervals = list(sorted(timeIntervals))

    for t in timeIntervals:
        data[t] = [0, 0]

    for i, row in df.iterrows():
        timeSpent = max(timeIntervals)
        for j, t in enumerate(timeIntervals):
            if row['TimeBefore'] - row['TimeAfter'] < t:
                timeSpent = t
                break

        xsDrop = functions.expectedScore(row['EvalBefore']) - functions.expectedScore(row['EvalAfter'])
        if xsDrop >= 10:
            data[timeSpent][0] += 1
        data[timeSpent][1] += 1

    print(data)
    plotData = list()
    for k, v in data.items():
        if v[1] == 0:
            plotData.append(0)
        else:
            plotData.append(v[0]/v[1])
    return plotData

if __name__ == '__main__':
    dataFile = '../resources/timeMistakes.pkl'
    pgns = ['../resources/grandSwiss2023Times.pgn', 
            '../resources/grandSwiss2025Times.pgn',
            '../resources/wijk2024Times.pgn', 
            '../resources/wijk2025Times.pgn', 
            '../resources/bundesligaTimes.pgn']
    # pgns = ['../resources/timeTest.pgn']
    ratings = [2500, 2600, 2700]
    times = [m*60 for m in [60, 50, 40, 30, 20, 10, 5, 0.99]]
    timesFull = [m*60 for m in [100, 80, 60, 40, 20, 1]]
    times30 = [m*60 for m in [40, 35, 30, 25, 20, 15, 10, 5, 1]]
    times30 = [m*60 for m in [30, 27, 24, 21, 18, 15, 12, 9, 6, 3, 1]]
    times40 = [m*60 for m in [40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 0.99]]
    times15 = [m*60 for m in [15, 12, 9, 6, 3, 1]]

    timeSpent = [10, 30, 60, 300, 600, 900, 1200]
    # df = extractMoveData(pgns)
    # with open(dataFile, 'wb') as f:
        # pickle.dump(df, f)

    with open(dataFile, 'rb') as f:
        df = pickle.load(f)
    print(df)
    catData = categoriseData(df, times15, ratings)
    plotData = list()
    for k, v in catData.items():
        plotData.append(list())
        for idk in v.values():
            if idk[-1] == 0:
                plotData[-1].append(0)
            else:
                plotData[-1].append((idk[1]+idk[2])/idk[3])
    # plotting_helper.plotLineChart(plotData, 'Time remaining', 'Relative number of mistakes', 'Relative number of mistakes depending on the clock time', ratings, xTicks = [int(t/60) for t in times15])
    plotting_helper.plotLineChart(getIMBdata(df, times, [5, 10, 20]), 'Time remaining in minutes', 'Relative number of moves', 'Relative number of inaccuracies, mistakes and blunders depending on remaining time', ['Inaccuracies', 'Mistakes', 'Blunders'], xTicks = [int(t/60) for t in times], colors=plotting_helper.getColors(['blue', 'yellow', 'red']), filename='../out/time/imb.png')
    """ Calculating the accuracy depending on the time left wasn't very insightful
    acc = getAccuracyData(df, times40)
    print(acc)
    plotting_helper.plotLineChart([acc], 'Time remaining in minutes', 'Accuracy', 'Accuracy depending on time left', ['Accuracy'], xTicks = [int(t/60) for t in times40], colors=plotting_helper.getColors(['blue', 'yellow', 'red']))
    """
    mTC = mistakesWithTimeControl(df, times40)
    # plotting_helper.plotLineChart(mTC, 'Time remaining in minutes', 'Relative number of mistakes', 'Relative number of mistakes before and after the time control', ['Before move 40', 'After move 40'], xTicks = [int(t/60) for t in times40], colors=plotting_helper.getColors(['blue', 'orange', 'red']), filename='../out/time/TC.png')
    mistakesTimeSpent = mistakesByTimeSpent(df, timeSpent)
    print(mistakesTimeSpent)
    # plotting_helper.plotLineChart([mistakesTimeSpent], 'Time spent in seconds', 'Relative number of mistakes', 'Relative number of mistakes in relation to the time spent on moves', ['Mistakes'], xTicks = [t for t in timeSpent], colors=plotting_helper.getColors(['blue', 'yellow', 'red']), filename='../out/time/moveTime.png')
