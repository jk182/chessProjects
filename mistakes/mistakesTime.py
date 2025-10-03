import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import pandas as pd


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

        if rating not in data.keys():
            data[rating] = dict()

        xsDrop = functions.expectedScore(row['EvalBefore']) - functions.expectedScore(row['EvalAfter'])
        if xsDrop < 0:
            print(xsDrop)
        
        if xsDrop < imbCutoffs[0]:
            index = None
        elif imbCutoffs[0] <= xsDrop < imbCutoffs[1]:
            index = 0
        elif imbCutoffs[1] <= xsDrop < imbCutoffs[2]:
            index = 1
        else:
            index = 2

        if time not in data[rating].keys():
            data[rating][time] = [0, 0, 0, 0]

        data[rating][time][3] += 1
        if index is not None:
            data[rating][time][index] += 1
    return data


if __name__ == '__main__':
    pgns = ['../resources/grandSwiss2023Times.pgn', 
            '../resources/grandSwiss2025Times.pgn',
            '../resources/wijk2024Times.pgn', 
            '../resources/wijk2025Times.pgn']
    ratings = [2500, 2600, 2700]
    times = [m*60 for m in [60, 45, 30, 15]]
    df = extractMoveData(pgns)
    print(categoriseData(df, times, ratings))
