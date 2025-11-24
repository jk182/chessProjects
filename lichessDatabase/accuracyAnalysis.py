import chess
import chess.pgn

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions, plotting_helper
import pickle

import matplotlib.pyplot as plt


def getAccuracy(basePath: str, ratings: list, timeControls: list, startMove: int = None) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = list()
        for tc in timeControls:
            print(rating, tc)
            accuracyData = [0, 0]
            with open(f'{basePath}{rating}_{tc}.pgn', 'r') as pgn:
                while game := chess.pgn.read_game(pgn):
                    lastEval = None
                    node = game
                    ply = 0

                    while not node.is_end():
                        node = node.variations[0]
                        if lastEval is None and node.eval() is not None:
                            lastEval = node.eval().white().score(mate_score=10000)
                            continue
                        if node.eval() is not None:
                            currentEval = node.eval().white().score(mate_score=10000)
                            if startMove is not None and ply/2 + 1 >= startMove:
                                if node.board().turn:
                                    factor = -1
                                else:
                                    factor = 1
                                accuracy = functions.accuracy(functions.expectedScore(lastEval*factor), functions.expectedScore(currentEval*factor))
                                accuracy = min(100, accuracy)
                                accuracyData[0] += accuracy
                                accuracyData[1] += 1
                            lastEval = currentEval
                        ply += 1
            data[rating].append(accuracyData)
    return data


def getIMB(basePath: str, ratings: list, timeControls: list, imb: list = [5, 10, 20]) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = list()
        for tc in timeControls:
            print(rating, tc)
            imbData = [0, 0, 0, 0]
            with open(f'{basePath}{rating}_{tc}.pgn', 'r') as pgn:
                while game := chess.pgn.read_game(pgn):
                    lastEval = None
                    node = game

                    while not node.is_end():
                        node = node.variations[0]
                        imbData[3] += 1
                        if lastEval is None and node.eval() is not None:
                            lastEval = node.eval().white().score(mate_score=10000)
                            continue
                        if node.eval() is not None:
                            currentEval = node.eval().white().score(mate_score=10000)
                            if node.board().turn:
                                factor = -1
                            else:
                                factor = 1
                            xsLoss = functions.expectedScore(lastEval*factor) - functions.expectedScore(currentEval*factor)
                            if xsLoss >= imb[2]:
                                imbData[2] += 1
                            elif xsLoss >= imb[1]:
                                imbData[1] += 1
                            elif xsLoss >= imb[0]:
                                imbData[0] += 1
                            lastEval = currentEval
            data[rating].append(imbData)
    return data


def openingAdvantage(basePath: str, ratings: list, timeControls: list, targetMove: int = 10) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = list()
        for tc in timeControls:
            print(rating, tc)
            resultData = dict()
            with open(f'{basePath}{rating}_{tc}.pgn', 'r') as pgn:
                while game := chess.pgn.read_game(pgn):
                    ply = 0
                    lastEval = None
                    node = game

                    while not node.is_end():
                        node = node.variations[0]
                        if int(ply/2) >= targetMove and node.eval() is not None:
                            cp = node.eval().white().score(mate_score=10000)
                            result = game.headers["Result"]
                            if result == "1-0":
                                points = 1
                            elif result == "1/2-1/2":
                                points = 0.5
                            elif result == "0-1":
                                points = 0
                            else:
                                print(f'Result {result} not found')
                                break
                            if cp < 0:
                                cp = -cp
                                points = 1-points

                            if cp in resultData.keys():
                                resultData[cp][0] += points
                                resultData[cp][1] += 1
                            else:
                                resultData[cp] = [points, 1]
                        ply += 1
            data[rating].append(resultData)
    return data


def groupOpeningData(openingData: dict, timeControls: list, cpWidth: int = 50, nGroups: int = 20):
    """
    This function groups the opening data generated by openingAdvantage(...) into groups based on the evaluation
    """
    newData = dict()
    groups = [int(cpWidth/2)+cpWidth*i for i in range(nGroups)]
    for rating, data in openingData.items():
        newData[rating] = dict()
        for j, d in enumerate(data):
            scores = dict()
            for g in groups:
                scores[g] = [0, 0]
            for k, v in d.items():
                if k < groups[0]:
                    g = groups[0]
                elif k > groups[-1]:
                    g = groups[-1]
                else:
                    for i in range(len(groups)-1):
                        if groups[i] < k <= groups[i+1]:
                            g = groups[i+1]
                            break
                scores[g][0] += v[0]
                scores[g][1] += v[1]
            tcScores = dict()
            for k, v in scores.items():
                if v[1] == 0:
                    tcScores[k] = 0
                else:
                    tcScores[k] = v[0]/v[1]
            newData[rating][timeControls[j]] = tcScores
    return newData


def plotOpeningData(groupedOpeningData: dict, ratings: list, timeControls: list):
    colors = plotting_helper.getColors(['blue', 'purple', 'violet', 'orange', 'green', 'darkgreen'])
    for rating in ratings:
        plottingData = list()
        for tc in timeControls:
            plottingData.append(list(groupedOpeningData[rating][tc].values()))
        plotting_helper.plotLineChart(plottingData, 'Evaluation', 'Score', f'Score of {rating} rated players in different time controls based on evaluation', [f'{int(tc.split("+")[0])//60}+{tc.split("+")[1]}' for tc in timeControls], xTicks=[50*i for i in range(len(plottingData[0]))], colors=colors)# , filename=f'../out/openingAdv/rating{rating}.png')


if __name__ == '__main__':
    basePath = '../out/lichessDB/analysed_300g_rating'
    ratings = [1200, 1600, 2000, 2200, 2400]
    r2 = [1200, 1600, 2000, 2200]
    r1200 = [1200]
    timeControls = ["60+0", "180+0", "300+0", "600+0"]
    tc2 = ["60+0", "120+1", "180+0", "180+2", "300+0", "300+3"]
    tc3 = ["120+1", "180+0", "180+2", "300+0", "300+3", "600+0", "600+5", "900+10"]

    """
    openingData = openingAdvantage(basePath, r2, tc3, targetMove=10)
    with open('../out/openingDataMove10-2.pkl', 'wb+') as f:
        pickle.dump(openingData, f)
    """
    with open('../out/openingDataMove10-2.pkl', 'rb+') as f:
        openingData = pickle.load(f)
    groupedOpeningData = groupOpeningData(openingData, tc3, nGroups=21)
    plotOpeningData(groupedOpeningData, ratings, tc3)
    # with open('../out/lichessAcc.pkl', 'rb') as f:
        # accData = pickle.load(f)

    # data = getAccuracy(basePath, ratings, timeControls, startMove=5)
    
    # with open('../out/lichessAcc.pkl', 'wb+') as f:
        # pickle.dump(data, f)
    """
    for rating, d in accData.items():
        print(rating, [round(float(x[0]/x[1]), 2) for x in d])
    for rating, d in data.items():
        print(rating, [round(float(x[0]/x[1]), 2) for x in d])
    """
    """
    imbData = getIMB(basePath, ratings, timeControls)
    with open('../out/lichessIMB.pkl', 'wb+') as f:
        pickle.dump(imbData, f)
    for rating, imb in imbData.items():
        print(rating, [[round(float(x[i]/x[3]), 3) for i in range(3)] for x in imb])
    """
