import chess
from chess import pgn
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper
import matplotlib.pyplot as plt
import pandas as pd


def getScoresForRatings(pgnPaths: list) -> dict:
    """
    This calculates the scores in the PGNs for a given rating against each opponent rating band
    """
    results = dict()
    ratingBands = list(range(2500, 3000, 50))
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                    print("No Elo")
                    continue
                wElo = int(game.headers['WhiteElo'])
                bElo = int(game.headers['BlackElo'])
                if wElo < min(ratingBands) or bElo < min(ratingBands):
                    continue
                for i, rating in enumerate(ratingBands):
                    if rating > wElo:
                        wEloBand = ratingBands[i-1]
                        break
                for i, rating in enumerate(ratingBands):
                    if rating > bElo:
                        bEloBand = ratingBands[i-1]
                        break
                result = game.headers['Result']
                if result == '1-0':
                    wPoints = 1
                    bPoints = 0
                elif result == '1/2-1/2':
                    wPoints = 0.5
                    bPoints = 0.5
                elif result == '0-1':
                    wPoints = 0
                    bPoints = 1
                else:
                    print(f'Result not found: {result}')
                    continue

                if wEloBand in results.keys():
                    if bEloBand in results[wEloBand].keys():
                        results[wEloBand][bEloBand][0] += wPoints
                        results[wEloBand][bEloBand][1] += 1
                    else:
                        results[wEloBand][bEloBand] = [wPoints, 1]
                else:
                    results[wEloBand] = dict()
                    results[wEloBand][bEloBand] = [wPoints, 1]
                if bEloBand in results.keys():
                    if wEloBand in results[bEloBand].keys():
                        results[bEloBand][wEloBand][0] += bPoints
                        results[bEloBand][wEloBand][1] += 1
                    else:
                        results[bEloBand][wEloBand] = [bPoints, 1]
                else:
                    results[bEloBand] = dict()
                    results[bEloBand][wEloBand] = [bPoints, 1]
    ret = dict()
    for k, v in results.items():
        ret[k] = dict()
        for k2, v2 in v.items():
            ret[k][k2] = round(v2[0]/v2[1], 2)
    return ret


def getScoreByRatingDiff(pgnPaths: list, width: int = 50, maxDiff: int = 500) -> dict:
    """
    This calculates the score from the higher rated player's perspective for each [width] point rating differnence
    """
    results = dict()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                    print("No Elo")
                    continue
                wElo = int(game.headers['WhiteElo'])
                bElo = int(game.headers['BlackElo'])

                if wElo >= bElo:
                    perspective = chess.WHITE
                else:
                    perspective = chess.BLACK
                
                diff = abs(wElo - bElo)
                if diff > maxDiff:
                    # print(f'Rating difference over {maxDiff} points')
                    continue

                diffBand = 0
                for i in range(0, maxDiff//width + 1):
                    if i*width - width/2 < diff <= i*width + width/2:
                        diffBand = i*width
                        break

                result = game.headers['Result']
                if (result == '1-0' and perspective == chess.WHITE) or (result == '0-1' and perspective == chess.BLACK):
                    points = 1
                elif (result == '1-0' and perspective == chess.BLACK) or (result == '0-1' and perspective == chess.WHITE):
                    points = 0
                elif result == '1/2-1/2':
                    points = 0.5
                else:
                    print(f'Result not found: {result}')
                    continue

                if diffBand in results.keys():
                    results[diffBand][0] += points
                    results[diffBand][1] += 1
                else:
                    results[diffBand] = [points, 1]
    scores = dict()
    for k, v in results.items():
        scores[k] = round(v[0]/v[1], 3)
    return dict(sorted(scores.items()))


def getTimeData(pgnPaths: list, startTime: int = 180) -> pd.DataFrame:
    data = dict()
    for key in ['MoveNr', 'EloDiff', 'TimeDiff', 'Eval', 'Result']:
        data[key] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                    print("No Elo")
                    continue
                result = game.headers['Result']
                if result not in ['1-0', '0-1', '1/2-1/2']:
                    print(f'Result not found: {result} in file {pgnPath}')
                
                moveNr = 0
                eloDiff = int(game.headers['WhiteElo']) - int(game.headers['BlackElo'])

                wClock = None
                bClock = None
                wEval = None
                bEval = None
                node = game
                while not node.is_end():
                    node = node.variations[0]
                    if not node.turn():
                        moveNr += 1

                    if result == '1-0':
                        wScore = 1
                        bScore = 0
                    elif result == '0-1':
                        wScore = 0
                        bScore = 1
                    else:
                        wScore = 0.5
                        bScore = 0.5
                    if not node.turn():
                        if node.clock() is not None:
                            wClock = int(node.clock())
                        if bClock is None or wClock is None:
                            continue
                        if node.eval() is not None:
                            wEval = node.eval().white().score()
                        if wEval is None:
                            continue
                        data['MoveNr'].append(moveNr)
                        data['Result'].append(wScore)
                        data['EloDiff'].append(eloDiff)
                        data['Eval'].append(wEval)
                        data['TimeDiff'].append(wClock - bClock)
                    else:
                        if node.clock() is not None:
                            bClock = int(node.clock())
                        if bClock is None or wClock is None:
                            continue
                        if node.eval() is not None:
                            bEval = node.eval().black().score()
                        if bEval is None: 
                            continue
                        data['MoveNr'].append(moveNr)
                        data['Result'].append(bScore)
                        data['EloDiff'].append(-eloDiff)
                        data['Eval'].append(bEval)
                        data['TimeDiff'].append(bClock - wClock)
    df = pd.DataFrame(data)
    return df


def analyseTimeData(timeData: pd.DataFrame, timeInterval: int = 15, startMove: int = 10, maxTime: int = 180):
    resultData = dict()

    for i, row in timeData.iterrows():
        time = row['TimeDiff']
        result = row['Result']
        ratingDiff = row['EloDiff']
        cp = row['Eval']
        for j in range(-maxTime//timeInterval, maxTime//timeInterval + 2):
            if j*timeInterval <= time < (j+1)*timeInterval:
                timeSlot = j*timeInterval
                break
        
        if timeSlot in resultData.keys():
            resultData[timeSlot][0] += result
            resultData[timeSlot][1] += 1
        else:
            resultData[timeSlot] = [result, 1]

    print(dict(sorted(resultData.items())))
    d = dict()
    for k, v in resultData.items():
        d[k] = float(v[0]/v[1])
    return dict(sorted(d.items()))


def plotScores(data: list, xLabel: str, yLabel: str, title:str, legend: list, filename: str = None):
    colors = plotting_helper.getDefaultColors()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(plotting_helper.getColor('background'))
    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    
    xMin = 200
    xMax = 0
    for i, d in enumerate(data):
        ax.plot(d[0], d[1], color=colors[i%len(colors)], label=legend[i])
        xMin = min(xMin, min(d[0]))
        xMax = max(xMax, max(d[0]))

    ax.legend()
    ax.set_xlim(xMin, xMax)
    ax.set_ylim(0, 1)
    plt.title(title)

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


if __name__ == '__main__':
    blitz = ['../resources/worldBlitz2023.pgn', '../resources/worldBlitz2024.pgn', '../resources/worldBlitz2022.pgn', '../resources/teamBlitz2025.pgn']
    """
    ratingScores = getScoresForRatings(blitz)
    for k, v in ratingScores.items():
        print(k, v)
    """
    rapid = ['../resources/worldRapid2023.pgn', '../resources/worldRapid2024.pgn', '../resources/worldRapid2022.pgn', '../resources/teamRapid2025.pgn']
    classical = ['../resources/germanBundesliga2025.pgn', '../resources/candidatesL.pgn', '../resources/olympiad2024.pgn', '../resources/wijk2025.pgn', '../resources/grandSwiss2023.pgn', '../resources/sharjah2024.pgn', '../resources/sharjah2025.pgn']

    # Basic Scores
    """
    rapidScores = getScoreByRatingDiff(rapid)
    blitzScores = getScoreByRatingDiff(blitz)
    classicalScores = getScoreByRatingDiff(classical)
    data = list()
    data.append([list(blitzScores.keys()), list(blitzScores.values())])
    data.append([list(rapidScores.keys()), list(rapidScores.values())])
    data.append([list(classicalScores.keys()), list(classicalScores.values())])
    for d in data:
        print(d)
    # plotScores(data, 'Rating difference', 'Score of the higher rated player', 'Scores of the higher rated players based on rating difference', ['Blitz', 'Rapid', 'Classical'], filename='../out/scoresByRatingDiff.png')
    """
    timeData = getTimeData(blitz)
    print(timeData)
    data = analyseTimeData(timeData)
    dataList = list()
    dataList.append([list(data.keys()), list(data.values())])
    plotScores(dataList, 'Rating difference', 'Score of the higher rated player', 'Scores of the higher rated players based on rating difference', ['Blitz', 'Rapid', 'Classical'])
