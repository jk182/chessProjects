import chess
import chess.pgn
import pickle

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper
from gameStatistics import gameAccuracy
import polars as pl
from scipy.stats import pearsonr


def getAccuraciesByYear(pgnPath: str, player: str, lichessAnalysis: bool = False) -> dict:
    """
    This gets the accuracies of a player and his opponents from a PGN file
    pgnPath: str
        Path to the PGN file
    player: str
        Name of the player
    lichessAnalysis: bool
        If this is true, the PGN file is assumed to have been analysed by Lichess
    return -> dict:
        {year: [(playerAccGame1, oppAccGame1), (playerAccGame2, oppAccGame2), ...], ...}
    """
    accData = dict()
    startEval = 20
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if player in game.headers["White"]:
                white = True
            elif player in game.headers["Black"]:
                white = False
            else:
                print(f'Player {player} not found in {game.headers["White"]}-{game.headers["Black"]}')

            year = int(game.headers["Date"].split('.')[0])

            if year not in accData:
                accData[year] = list()

            evals = [startEval]

            node = game
            while not node.is_end():
                node = node.variations[0]
                if lichessAnalysis:
                    if node.eval():
                        cp = int(node.eval().white().score(mate_score=10000))
                    else:
                        cp = evals[-1]
                        # print('No evaluation found')
                else:
                    if not functions.readComment(node, True, True):
                        cp = evals[-1]
                        # print('No evaluation found')
                    else:
                        cp = functions.readComment(node, True, True)[1]

                evals.append(cp)

            axsl = gameAccuracy.calculateGeneralisedMean(evals)
            if white:
                playerAcc = functions.gameAccuracy(axsl[0])
                oppAcc = functions.gameAccuracy(axsl[1])
            else:
                playerAcc = functions.gameAccuracy(axsl[1])
                oppAcc = functions.gameAccuracy(axsl[0])

            accData[year].append((playerAcc, oppAcc))

    accData = dict(sorted(accData.items()))
    return accData


def extractAccuracyData(pgnPath: str, lichessAnalysis: bool = False) -> pl.DataFrame:
    data = dict()
    keys = ["White", "Black", "WhiteElo", "BlackElo", "GameDate", "Result", "Event", "WhiteAccuracy", "BlackAccuracy", "WhiteOpeningAcc", "BlackOpeningAcc", "WhiteMiddlegameAcc", "BlackMiddlegameAcc", "WhiteEndgameAcc", "BlackEndgameAcc"]

    for key in keys:
        data[key] = list()

    startEval = 20
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            evals = [startEval]
            node = game
            openingEndIndex = None
            middlegameEndIndex = None
            lastGamePhase = "opening"

            while not node.is_end():
                node = node.variations[0]
                currentGamePhase = functions.getGamePhase(node.board())
                if currentGamePhase != lastGamePhase:
                    lastGamePhase = currentGamePhase
                    if lastGamePhase == "middlegame":
                        openingEndIndex = len(evals)
                    elif lastGamePhase == "endgame":
                        middlegameEndIndex = len(evals)

                if lichessAnalysis:
                    if node.eval():
                        cp = int(node.eval().white().score(mate_score=10000))
                    else:
                        cp = evals[-1]
                else:
                    if not functions.readComment(node, True, True):
                        cp = evals[-1]
                    else:
                        cp = functions.readComment(node, True, True)[1]

                evals.append(cp)

            axsl = gameAccuracy.calculateGeneralisedMean(evals)

            if openingEndIndex is not None:
                openingAXSL = gameAccuracy.calculateGeneralisedMean(evals[:openingEndIndex])
            else:
                openingAXSL = (None, None)
                middlegameAXSL = (None, None)
                endgameAXSL = (None, None)
            if middlegameEndIndex is not None:
                middlegameAXSL = gameAccuracy.calculateGeneralisedMean(evals[openingEndIndex:middlegameEndIndex], whiteStart = (openingEndIndex%2 == 0))
                endgameAXSL = gameAccuracy.calculateGeneralisedMean(evals[middlegameEndIndex:], whiteStart=(middlegameEndIndex%2 == 0))
            else:
                middlegameAXSL = (None, None)
                endgameAXSL = (None, None)

            gameData = [
                    game.headers["White"],
                    game.headers["Black"],
                    int(game.headers["WhiteElo"]),
                    int(game.headers["BlackElo"]),
                    game.headers["Date"],
                    game.headers["Result"],
                    game.headers["Event"],
                    functions.gameAccuracy(axsl[0]),
                    functions.gameAccuracy(axsl[1]),
                    functions.gameAccuracy(openingAXSL[0]),
                    functions.gameAccuracy(openingAXSL[1]),
                    functions.gameAccuracy(middlegameAXSL[0]),
                    functions.gameAccuracy(middlegameAXSL[1]),
                    functions.gameAccuracy(endgameAXSL[0]),
                    functions.gameAccuracy(endgameAXSL[1])]

            for i, key in enumerate(keys):
                data[key].append(gameData[i])

    return pl.DataFrame(data)


def playerAccuracyByResult(gameData: pl.DataFrame, playerName: str) -> dict:
    resultData = [[list(), list()], [list(), list()], [list(), list()]]
    for row in gameData.iter_rows(named=True):
        if playerName in row["White"]:
            white = True
        elif playerName in row["Black"]:
            white = False
        else:
            continue

        if white:
            playerAccuracy = row["WhiteAccuracy"]
            opponentAccuracy = row["BlackAccuracy"]
        else:
            playerAccuracy = row["BlackAccuracy"]
            opponentAccuracy = row["WhiteAccuracy"]

        if row["Result"] == "1/2-1/2":
            resultData[1][0].append(playerAccuracy)
            resultData[1][1].append(opponentAccuracy)
        elif (row["Result"] == "1-0" and white) or (row["Result"] == "0-1" and not white):
            resultData[0][0].append(playerAccuracy)
            resultData[0][1].append(opponentAccuracy)
        else:
            resultData[2][0].append(playerAccuracy)
            resultData[2][1].append(opponentAccuracy)

    returnData = list()
    for data in resultData:
        returnData.append([sum(d)/len(d) for d in data])
    return returnData


def getPlayerAccuracyByRating(gameData: pl.DataFrame, playerName: str) -> dict:
    data = []
    for row in gameData.iter_rows(named=True):
        if playerName in row["White"]:
            white = True
        elif playerName in row["Black"]:
            white = False
        else:
            continue

        result = row["Result"]
        if result == "1/2-1/2":
            points = 0.5

        if white:
            playerRating = row["WhiteElo"]
            playerAcc = row["WhiteAccuracy"]
            playerOpeningAcc = row["WhiteOpeningAcc"]
            playerMiddlegameAcc = row["WhiteMiddlegameAcc"]
            playerEndgameAcc = row["WhiteEndgameAcc"]
            opponentRating = row["BlackElo"]
            opponentAcc = row["BlackAccuracy"]
            opponentOpeningAcc = row["BlackOpeningAcc"]
            opponentMiddlegameAcc = row["BlackMiddlegameAcc"]
            opponentEndgameAcc = row["BlackEndgameAcc"]
            if result == "1-0":
                points = 1
            elif result == "0-1":
                points = 0
        else:
            playerRating = row["BlackElo"]
            playerAcc = row["BlackAccuracy"]
            playerOpeningAcc = row["BlackOpeningAcc"]
            playerMiddlegameAcc = row["BlackMiddlegameAcc"]
            playerEndgameAcc = row["BlackEndgameAcc"]
            opponentRating = row["WhiteElo"]
            opponentAcc = row["WhiteAccuracy"]
            opponentOpeningAcc = row["WhiteOpeningAcc"]
            opponentMiddlegameAcc = row["WhiteMiddlegameAcc"]
            opponentEndgameAcc = row["WhiteEndgameAcc"]
            if result == "1-0":
                points = 0
            elif result == "0-1":
                points = 1

        data.append((playerRating, opponentRating, playerAcc, opponentAcc, playerOpeningAcc, opponentOpeningAcc, playerMiddlegameAcc, opponentMiddlegameAcc, playerEndgameAcc, opponentEndgameAcc, points))
    return data


def getMovingAverageAccuracy(gameData: pl.DataFrame, playerName: str, windowSize: int = 20, relative: bool = False) -> list:
    data = list()
    for row in gameData.iter_rows(named=True):
        if playerName in row["White"]:
            white = True
        elif playerName in row["Black"]:
            white = False
        else:
            continue

        if white:
            if relative:
                accuracy = row["WhiteAccuracy"] - row["BlackAccuracy"]
            else:
                accuracy = row["WhiteAccuracy"]
            perfRating = row["BlackElo"]
        else:
            if relative:
                accuracy = row["BlackAccuracy"] - row["WhiteAccuracy"]
            else:
                accuracy = row["BlackAccuracy"]
            perfRating = row["WhiteElo"]
        
        result = row["Result"]
        if (result == "1-0" and white) or (result == "0-1" and not white):
            perfRating += 400
            points = 1
        elif (result == "1-0" and not white) or (result == "0-1" and white):
            perfRating -= 400
            points = 0
        else:
            points = 0.5

        data.append((row["GameDate"], accuracy, perfRating, points))

    data = list(sorted(data))
    accuracies = [d[1] for d in data]
    perfRatings = [d[2] for d in data]
    movingAverage = [sum(accuracies[i-windowSize:i])/windowSize for i in range(windowSize, len(accuracies))]
    movingAverageRatings = [sum(perfRatings[i-windowSize:i])/windowSize for i in range(windowSize, len(perfRatings))]
    points = [d[3] for d in data]
    movingAvgPoints = [sum(points[i-windowSize:i])/windowSize for i in range(windowSize, len(points))]
    return [(data[i+windowSize][0], movingAverage[i], movingAverageRatings[i], movingAvgPoints[i]) for i in range(len(movingAverage))]


def getPlayerAccuracyByGamePhaseAndDate(gameData: pl.DataFrame, playerName: str, windowSize: int = 20) -> list:
    data = list()
    for row in gameData.iter_rows(named=True):
        if playerName in row["White"]:
            white = True
        elif playerName in row["Black"]:
            white = False
        else:
            continue

        if white:
            accuracy = row["WhiteAccuracy"]
            openingAcc = row["WhiteOpeningAcc"]
            middlegameAcc = row["WhiteMiddlegameAcc"]
            endgameAcc = row["WhiteEndgameAcc"]
            perfRating = row["BlackElo"]
        else:
            accuracy = row["BlackAccuracy"]
            openingAcc = row["BlackOpeningAcc"]
            middlegameAcc = row["BlackMiddlegameAcc"]
            endgameAcc = row["BlackEndgameAcc"]
            perfRating = row["WhiteElo"]
        
        result = row["Result"]
        if (result == "1-0" and white) or (result == "0-1" and not white):
            perfRating += 400
        elif (result == "1-0" and not white) or (result == "0-1" and white):
            perfRating -= 400

        data.append((row["GameDate"], accuracy, openingAcc, middlegameAcc, endgameAcc, perfRating, points))

    data = list(sorted(data))
    perfRatings = [d[5] for d in data]
    movingAverageRatings = [sum(perfRatings[i-windowSize:i])/windowSize for i in range(windowSize, len(perfRatings))]
    returnData = [[data[i+windowSize][0], movingAverageRatings[i]] for i in range(len(movingAverageRatings))]
    for i in range(1, 5):
        accuracies = [d[i] for d in data]
        movingAverage = list()
        for j in range(windowSize, len(accuracies)):
            acc = [a for a in accuracies[j-windowSize:j] if a is not None]
            if len(acc) == 0:
                print("Windows too small")
                movingAverage.append(0)
            else:
                movingAverage.append(sum(acc)/len(acc))
        for k in range(len(returnData)):
            returnData[k].append(movingAverage[k])

    return returnData


def getAccuracyByOpponentRating(gameData: pl.DataFrame, playerName: str, minRating: int = 2500, maxRating: int = 2850, ratingGroupWidth: int = 25) -> dict:
    ratingData = dict()
    for rating in range(minRating, maxRating+ratingGroupWidth+1, ratingGroupWidth):
        ratingData[rating] = list()

    for row in gameData.iter_rows(named=True):
        result = row["Result"]
        if playerName in row["White"]:
            opponentRating = row["BlackElo"]
            playerAccuracy = row["WhiteAccuracy"]
            opponentAccuracy = row["BlackAccuracy"]
            playerOpeningAcc = row["WhiteOpeningAcc"]
            playerMiddlegameAcc = row["WhiteMiddlegameAcc"]
            playerEndgameAcc = row["WhiteEndgameAcc"]
            opponentOpeningAcc = row["BlackOpeningAcc"]
            opponentMiddlegameAcc = row["BlackMiddlegameAcc"]
            opponentEndgameAcc = row["BlackEndgameAcc"]
            if result == "1-0":
                points = 1
            elif result == "1/2-1/2":
                points = 0.5
            else:
                points = 0
        elif playerName in row["Black"]:
            opponentRating = row["WhiteElo"]
            playerAccuracy = row["BlackAccuracy"]
            opponentAccuracy = row["WhiteAccuracy"]
            playerOpeningAcc = row["BlackOpeningAcc"]
            playerMiddlegameAcc = row["BlackMiddlegameAcc"]
            playerEndgameAcc = row["BlackEndgameAcc"]
            opponentOpeningAcc = row["WhiteOpeningAcc"]
            opponentMiddlegameAcc = row["WhiteMiddlegameAcc"]
            opponentEndgameAcc = row["WhiteEndgameAcc"]
            if result == "1-0":
                points = 0
            elif result == "1/2-1/2":
                points = 0.5
            else:
                points = 1
        else:
            continue
        
        ratingIndex = maxRating+ratingGroupWidth
        for rating in ratingData.keys():
            if opponentRating <= rating:
                ratingIndex = rating
                break

        ratingData[ratingIndex].append((playerAccuracy, opponentAccuracy, points, playerOpeningAcc, opponentOpeningAcc, playerMiddlegameAcc, opponentMiddlegameAcc, playerEndgameAcc, opponentEndgameAcc))

    returnData = dict()
    keys = ["PlayerAccuracy", "OpponentAccuracy", "PlayerWinAccuracy", "PlayerDrawAccuracy", "PlayerLossAccuracy", "AvgPoints", "DrawPercentage", "PlayerOpeningAcc", "OpponentOpeningAcc", "PlayerMiddlegameAcc", "OpponentMiddlegameAcc", "PlayerEndgameAcc", "OpponentEndgameAcc"]
    for rating, data in ratingData.items():
        if len(data) == 0:
            continue
        playerAcc = sum([d[0] for d in data])/len(data)
        opponentAcc = sum([d[1] for d in data])/len(data)
        winAcc = sum([d[0] for d in data if d[2] == 1])/max(1, len([d[0] for d in data if d[2] == 1]))
        drawAcc = sum([d[0] for d in data if d[2] == 0.5])/max(1, len([d[0] for d in data if d[2] == 0.5]))
        lossAcc = sum([d[0] for d in data if d[2] == 0])/max(1, len([d[0] for d in data if d[2] == 0]))
        points = sum([d[2] for d in data])/len(data)
        drawPercentage = sum([1 for d in data if d[2] == 0.5])/len(data)
        dataList = [playerAcc, opponentAcc, points, drawPercentage, winAcc, drawAcc, lossAcc]
        for i in range(3, len(data[0])):
            acc = [d[i] for d in data if d[i] is not None]
            if len(acc) == 0:
                dataList.append(None)
            else:
                dataList.append(sum(acc)/len(acc))

        returnData[rating] = dict()
        for i, k in enumerate(keys):
            returnData[rating][k] = dataList[i]

    return returnData



if __name__ == '__main__':
    pgn = '../out/carlsenClassicalAnalysed.pgn'
    # accData = getAccuraciesByYear(pgn, 'Carlsen')
    # pgn = '../out/capablancaTournamentGames_analysed.pgn'
    pgns = ['../out/capablancaTournamentGames_analysed.pgn', '../out/alekhineTournamentGames_analysed.pgn', '../out/botvinnikGamesAnalysed.pgn', '../out/talGamesAnalysed.pgn', '../out/carlsenClassicalAnalysed.pgn']
    names = ['Capablanca', 'Alekhine', 'Botvinnik', 'Tal', 'Carlsen']
    pgns = ['../out/carlsenClassicalAnalysed.pgn']
    names = ['Carlsen']
    # accData = getAccuraciesByYear(pgn, 'Capablanca')
    """
    for i in range(len(pgns)):
        pgn = pgns[i]
        name = names[i]
        accData = getAccuraciesByYear(pgn, name)
        print(name)
        for k, v in accData.items():
            p = sum([x[0] for x in v])/len(v)
            o = sum([x[1] for x in v])/len(v)
            print(k, round(p, 2), round(o, 2), round(p-o, 2))

        for i in range(2):
            total = sum([sum([x[i] for x in v])/len(v) for v in accData.values()]) / len(accData)
            print(round(total, 3))
    """

    """
    gameData = extractAccuracyData(pgn)
    with open('../out/carlsenAccuracyData.pkl', 'wb+') as f:
        pickle.dump(gameData, f)
    """

    with open('../out/carlsenAccuracyData.pkl', 'rb') as f:
        gameData = pickle.load(f)

    accData = getPlayerAccuracyByRating(gameData, 'Carlsen')
    openingAcc = [d[4] for d in accData if d[4] is not None]
    openingAccOpp = [d[5] for d in accData if d[5] is not None]
    middlegameAcc = [d[6] for d in accData if d[6] is not None]
    middlegameAccOpp = [d[7] for d in accData if d[7] is not None]
    endgameAcc = [d[8] for d in accData if d[8] is not None]
    endgameAccOpp = [d[9] for d in accData if d[9] is not None]
    plotData = list()
    for d in [(openingAcc, openingAccOpp), (middlegameAcc, middlegameAccOpp), (endgameAcc, endgameAccOpp)]:
        plotData.append([sum(d[0])/len(d[0]), sum(d[1])/len(d[1])])
        
    plotting_helper.plotPlayerBarChart(plotData, ['Opening', 'Middlegame', 'Endgame'], 'Accuracy', 'Accuracy by game phase', ['Carlsen accuracy', 'Opponent accuracy'], filename='../out/accuracyByGamePhase.png')

    # Accuracy by game phase and result. This isn't informative, because the player who wins has on average a higher accuracy in every phase of the game
    """
    plotData = list()
    for points in [1, 0.5, 0]:
        d = list()
        for i in range(4, 10):
            acc = [d[i] for d in accData if d[i] is not None and d[10] == points]
            d.append(sum(acc)/len(acc))
        plotData.append(d)

    plotting_helper.plotPlayerBarChart(plotData, ['Carlsen win', 'Draw', 'Carlsen loss'], 'Accuracy', 'Accuracy by game phase and result', ['Carlsen opening', 'Opponent opening', 'Carlsen middlegame', 'Opponent middlegame', 'Carlsen endgame', 'Opponent endgame'])
    """

    # Accuracy of Carlsen and opponents based on game outcome
    # resultData = playerAccuracyByResult(gameData, 'Carlsen')
    # plotting_helper.plotPlayerBarChart(resultData, ['Carlsen win', 'Draw', 'Carlsen loss'], 'Accuracy', 'Accuracy of Carlsen and his opponents based on the game result', ['Carlsen accuracy', 'Opponent accuracy'], filename='../out/accuracyByGameResult.png')


    minRating = 2450
    maxRating = 2800
    ratingGroupWidth = 50
    ratingData = getAccuracyByOpponentRating(gameData, 'Carlsen', minRating=minRating, maxRating=maxRating, ratingGroupWidth=ratingGroupWidth)
    """
    for k, v in ratingData.items():
        print(k, [(k, round(d, 3)) for k, d in v.items()])
    """

    keys = ["PlayerOpeningAcc", "OpponentOpeningAcc", "PlayerMiddlegameAcc", "OpponentMiddlegameAcc", "PlayerEndgameAcc", "OpponentEndgameAcc"]
    legend = ["Carlsen opening accuracy", "Opponent opening accuracy", "Carlsen middlegame accuracy", "Opponent middlegame accuracy", "Carlsen endgame accuracy", "Opponent endgame accuracy"] 
    xTickLabels = [f'< {rating}' if rating == minRating else f'{rating-ratingGroupWidth}-{rating}' if rating <= maxRating else f'{rating-ratingGroupWidth}+' for rating in range(minRating, maxRating+ratingGroupWidth+1, ratingGroupWidth)]
    ratingPlotData = [[v[key] for key in keys] for v in ratingData.values()]
    # for d in ratingPlotData:
        # print([round(x, 2) for x in d])
        # print([d[i]-d[i+1] for i in range(0, len(d), 2)])
    # plotting_helper.plotPlayerBarChart(ratingPlotData, xTickLabels, "Accuracy", "Accuracy of Carlsen and opponents by opponent rating and game phase", legend, colors=plotting_helper.getColors(["blue", "darkblue", "yellow", "darkorange", "slightly better", "much better"]), xlabel='Opponent rating', filename='../out/accuracyByRatingAndGamePhase.png', ncol=3, loc='upper right', fontsize=9,)
    # ratingData = getAccuracyByOpponentRating(gameData, 'Carlsen', ratingGroupWidth=25)
    # plotData = [v["PlayerAccuracy"] for v in ratingData.values()]
    # drawPercentage = [v["DrawPercentage"] for v in ratingData.values()]
    # plotting_helper.plotLineChartSingleX([plotData, drawPercentage], 'Opponent rating', 'Accuracy', "Carlsen's accuracy by the rating of his opponents", ['Carlsen accuracy', 'Draw percentage'], xTicks=list(ratingData.keys()), multipleY=True)
    # movingAvgGamePhase = getPlayerAccuracyByGamePhaseAndDate(gameData, 'Carlsen')
    # plotting_helper.plotLineChartSingleX([[m[i] for m in movingAvgGamePhase] for i in range(2, 6)], 'Date', 'Accuracy', 'Carlsen accuracy by date', ['Accuracy', 'Opening accuracy', 'Middlegame accuracy', 'Endgame accuracy'], xTicks=[m[0] for m in movingAvgGamePhase], xTickFactor=80)

    # Moving average of accuracy and points per game/performance rating
    # movingAvg = getMovingAverageAccuracy(gameData, 'Carlsen')
    # plotting_helper.plotLineChartSingleX([[m[1] for m in movingAvg], [m[3] for m in movingAvg]], 'Date', 'Accuracy', "Carlsen's average accuracy and points per game over time", ['Accuracy', 'Points per game'], xTicks=[m[0] for m in movingAvg], xTickFactor=100, multipleY=True, secondYLabel='Points per game', colors=plotting_helper.getColors(['darkorange', 'blue']), filename='../out/accuracyAvgWithPoints.png')
    # plotting_helper.plotLineChartSingleX([[m[1] for m in movingAvg], [m[2] for m in movingAvg]], 'Date', 'Accuracy', 'Carlsen accuracy by date', ['Carlsen', 'Performance rating'], xTicks=[m[0] for m in movingAvg], xTickFactor=80, multipleY=True)
    """
    evals = [20, 30, 30, 40, 20, 0]
    evals = [-1*e for e in evals]
    print(functions.lichessGameAccuracy(evals, whiteStart=False))
    """
    """
    accData = getPlayerAccuracyByRating(gameData, 'Carlsen')
    xVals = [[d[i] for d in accData] for i in [2, 3, 2]]
    yVals = [[d[i] for d in accData] for i in [0, 1, 1]]
    plotting_helper.plotScatterPlot(xVals, yVals, 'Accuracy', 'Rating', 'Accuracy by rating', legend=['Carlsen', 'Opponents', 'Carlsen by opp'], alpha=0.5)
    for i in range(3):
        print(pearsonr(xVals[i], yVals[i]))
    """
