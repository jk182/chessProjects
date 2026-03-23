import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper
import matplotlib.pyplot as plt


def getPlayerRatings(pgnPath: str) -> dict:
    """
    This function extracts the players with their ratings from the given PGN
    """
    playerRatings = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]
            whiteElo = int(game.headers["WhiteElo"])
            blackElo = int(game.headers["BlackElo"])

            if white not in playerRatings:
                playerRatings[white] = whiteElo
            if black not in playerRatings:
                playerRatings[black] = blackElo

    return playerRatings


def getPlayerResults(pgnPath: str) -> dict:
    """
    This function gets the result of each player against each other
    return -> dict
        {player: {opponent1: [(game1points, game1color, roundNr), (game2points, game2color, roundNr), ...], opponent2: ...}}
    """
    results = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]
            result = game.headers["Result"]
            if "." in game.headers["Round"]:
                roundNr = int(game.headers["Round"].split(".")[0])
            else:
                roundNr = int(game.headers["Round"])

            if result == '1-0':
                whitePoints = 1
                blackPoints = 0
            elif result == '1/2-1/2':
                whitePoints = 0.5
                blackPoints = 0.5
            elif result == '0-1':
                whitePoints = 0
                blackPoints = 1
            else:
                print(f'Result not found: {result}')

            if white not in results:
                results[white] = dict()
            if black not in results:
                results[black] = dict()

            if black not in results[white]:
                results[white][black] = [(whitePoints, True, roundNr)]
            else:
                results[white][black].append((whitePoints, True, roundNr))

            if white not in results[black]:
                results[black][white] = [(blackPoints, False, roundNr)]
            else:
                results[black][white].append((blackPoints, False, roundNr))
    return results


def getRoundByRoundResults(pgnPath: str) -> dict:
    """
    This function gets the result for each player in every round
    return -> dict:
        {playerName: [round1Result, round2Result, ...], ...}
    """
    roundResults = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]

            if white not in roundResults:
                roundResults[white] = list()
            if black not in roundResults:
                roundResults[black] = list()

            result = game.headers["Result"]
            if result == "1-0":
                wPoints = 1
                bPoints = 0
            elif result == "1/2-1/2":
                wPoints = 0.5
                bPoints = 0.5
            elif result == "0-1":
                wPoints = 0
                bPoints = 1
            else:
                print(f'Result not found: {result} in game {white}-{black}')
                continue

            roundResults[white].append(wPoints)
            roundResults[black].append(bPoints)

    return roundResults


def getScoresVersusSeeds(pgnPath: str, useFinalRankings: bool = False) -> dict:
    """
    This calculates the score for each player against the different seeds
    return -> dict:
        {player: [pointsVsSeed1, pointsVsSeed2, ...], ...}
        The score is None for the seed of the player themselves
    """
    playerResults = getPlayerResults(pgnPath)

    if useFinalRankings:
        seeds = getPlayerRankings(playerResults)
    else:
        ratings = getPlayerRatings(pgnPath)
        seeds = list(dict(reversed(sorted(ratings.items(), key=lambda x: x[1]))).keys())

    scoresVsSeeds = dict()
    for player in seeds:
        scoresVsSeeds[player] = [0] * len(seeds)

    for player in scoresVsSeeds:
        for seed, opponent in enumerate(seeds):
            if not player == opponent:
                score = sum([s[0] for s in playerResults[player][opponent]])
                scoresVsSeeds[player][seed] = score
            else:
                scoresVsSeeds[player][seed] = None
    return scoresVsSeeds


def getGameResultsPerRound(pgnPath: str) -> list:
    """
    This returns a list containing the number of white wins, draws and black wins in each round
    """
    gameResultsPerRound = list()
    lastRound = None
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if "." in game.headers["Round"]:
                roundNr = int(game.headers["Round"].split(".")[0])
            else:
                roundNr = int(game.headers["Round"])

            if lastRound is None:
                lastRound = roundNr
                wdl = [0, 0, 0]

            if roundNr != lastRound:
                lastRound = roundNr
                gameResultsPerRound.append(wdl)
                wdl = [0, 0, 0]

            result = game.headers["Result"]
            if result == "1-0":
                wdl[0] += 1
            elif result == "1/2-1/2":
                wdl[1] += 1
            elif result == "0-1":
                wdl[2] += 1
            else:
                print(f'Result not found: {result} in game {game.headers["White"]}-{game.headers["Black"]}')
                continue

    gameResultsPerRound.append(wdl)
    return gameResultsPerRound


def getPlayerRankings(playerResults: dict) -> list:
    """
    This function calculates the final ranking of each player, based on the results from getPlayerResults
    """
    points = dict()
    for player, results in playerResults.items():
        rounds = list(results.values())
        points[player] = sum([v[0] for r in rounds for v in r])

    rankings = list(dict(reversed(sorted(points.items(), key=lambda v: v[1]))).keys())
    
    # dealing with tied players
    # TODO: include SB, three-way ties
    for i, player in enumerate(rankings[:-1]):
        nextP = rankings[i+1]
        if points[player] == points[nextP]:
            h2h = sum([result[0] for result in playerResults[player][nextP]]) 
            if h2h > 1:
                continue
            elif h2h < 1:
                rankings[i] = nextP
                rankings[i+1] = player
            else:
                winsP = sum([r[0] for result in playerResults[player].values() for r in result if r[0] == 1])
                winsNP = sum([r[0] for result in playerResults[nextP].values() for r in result if r[0] == 1])
                if winsP > winsNP:
                    continue
                elif winsNP > winsP:
                    rankings[i] = nextP
                    rankings[i+1] = player

    return rankings


def getPlayerAccuracies(pgnPath: str) -> dict:
    """
    This gets the average accuracy of every player over the tournament
    """
    accuracies = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]

            if white not in accuracies:
                accuracies[white] = [[0, 0], [0, 0]]
            if black not in accuracies:
                accuracies[black] = [[0, 0], [0, 0]]

            node = game
            cpB = None

            while not node.is_end():
                node = node.variations[0]

                if not functions.readComment(node, True, True):
                    continue
                cpA = functions.readComment(node, True, True)[1]

                if cpB is not None:
                    if node.turn():
                        xsB = functions.expectedScore(cpB * -1)
                        xsA = functions.expectedScore(cpA * -1)
                        acc = functions.accuracy(xsB, xsA)
                        accuracies[black][0][0] += acc
                        accuracies[black][0][1] += 1
                        accuracies[white][1][0] += acc
                        accuracies[white][1][1] += 1
                    else:
                        factor = 1
                        player = white
                        xsB = functions.expectedScore(cpB)
                        xsA = functions.expectedScore(cpA)
                        acc = functions.accuracy(xsB, xsA)
                        accuracies[white][0][0] += acc
                        accuracies[white][0][1] += 1
                        accuracies[black][1][0] += acc
                        accuracies[black][1][1] += 1
                cpB = cpA

    avgAcc = dict()
    for player, accData in accuracies.items():
        avgAcc[player] = [0, 0]
        for i in range(2):
            avgAcc[player][i] = round(float(accData[i][0]/accData[i][1]), 3)

    return avgAcc


def getPlayerOpportunities(pgnPath: str) -> dict:
    """
    This function counts how often players got opportunities with a better position during the tournament
    return -> dict:
        {playerNames: [[totalOpp, gamesWithOpp, wonGames], [opponentTotalOpp, gamesWithOpponentOpp, lostGames]], ...}
    """
    opportunities = dict()
    cpThreshold = 100
    factor = 0.8

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]
            result = game.headers["Result"]

            if white not in opportunities:
                opportunities[white] = [[0, 0, 0], [0, 0, 0]]
            if black not in opportunities:
                opportunities[black] = [[0, 0, 0], [0, 0, 0]]

            node = game
            whiteAdvantage = False
            blackAdvantage = False
            wGameCounted = False
            bGameCounted = False
            while not node.is_end():
                node = node.variations[0]

                if not functions.readComment(node, True, True):
                    continue

                cpEval = functions.readComment(node, True, True)[1]

                if -cpThreshold * factor < cpEval < cpThreshold * factor:
                    whiteAdvantage = False
                    blackAdvantage = False
                elif cpEval >= cpThreshold and not whiteAdvantage:
                    whiteAdvantage = True
                    blackAdvantage = False
                    opportunities[white][0][0] += 1
                    opportunities[black][1][0] += 1
                    if not wGameCounted:
                        wGameCounted = True
                        opportunities[white][0][1] += 1
                        opportunities[black][1][1] += 1
                elif cpEval <= -cpThreshold and not blackAdvantage:
                    whiteAdvantage = False
                    blackAdvantage = True
                    opportunities[white][1][0] += 1
                    opportunities[black][0][0] += 1
                    if not bGameCounted:
                        bGameCounted = True
                        opportunities[white][1][1] += 1
                        opportunities[black][0][1] += 1

            if result == '1-0':
                opportunities[white][0][2] += 1
                opportunities[black][1][2] += 1
            elif result == '0-1':
                opportunities[white][1][2] += 1
                opportunities[black][0][2] += 1

    return opportunities


def getPlayerSharpnessChange(pgnPath: str, evalCutoff: int = 100) -> dict:
    """
    This calculates the average sharpness change per player
    evalCutoff: int
        If the evaluation drops by more than this cutoff, the change won't be counted
    """
    sharpChange = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]

            if white not in sharpChange:
                sharpChange[white] = list()
            if black not in sharpChange:
                sharpChange[black] = list()

            lastSharp = None
            lastEval = None

            node = game
            while not node.is_end():
                node = node.variations[0]

                if not functions.readComment(node, True, True):
                    continue

                wdl, cpEval = functions.readComment(node, True, True)
                sharp = functions.sharpnessLC0(wdl)

                if lastSharp is None or lastEval is None:
                    lastSharp = sharp
                    lastEval = cpEval
                    continue

                if abs(lastEval - cpEval) <= evalCutoff:
                    if node.turn:
                        sharpChange[black].append(sharp-lastSharp)
                    else:
                        sharpChange[white].append(sharp-lastSharp)

                lastSharp = sharp
                lastEval = cpEval

    return sharpChange


def plotPointsScoredAgainstSeeds(pgnPaths: list, xTickLabels: list, nPlayers: int = 3, useFinalRankings: bool = False, filename: str = None):
    plotData = list()
    for pgnPath in pgnPaths:
        pgnData = list()
        playerResults = getPlayerResults(pgnPath)
        rankings = getPlayerRankings(playerResults)
        scoresVsSeeds = getScoresVersusSeeds(pgnPath, useFinalRankings)

        if useFinalRankings:
            seeds = rankings
        else:
            seeds = list(dict(reversed(sorted(getPlayerRatings(pgnPath).items(), key=lambda x: x[1]))).keys())
        
        for i, seed in enumerate(seeds):
            pgnData.append([scoresVsSeeds[player][i] for player in rankings[:nPlayers]])

        plotData.append(pgnData)

    avgData = list()
    for i in range(len(seeds)):
        avgData.append([sum([v[i][j] for v in plotData if v[i][j] is not None])/max(1, len([v[i][j] for v in plotData if v[i][j] is not None])) for j in range(nPlayers)]) # entries with None would be games by the player against themselves, which are excluded from the average

    plotting_helper.plotPlayerBarChart(avgData, [i+1 for i in range(len(seeds))], 'Number of points', 'Average number of points scored by the top 3 finishers against the different seeds per tournament', ['Winner', 'Second place', 'Third place'], xlabel='Opponent seed by rating', legendUnderPlot=True, filename=filename)


def plotRoundByRoundScores(pgnPaths: list, nPlayers: int = 3, useCurrentHighestRanking: bool = True, filename: str = None):
    """
    This plots the average score after each round for the top n players
    pgnPaths: list
        List of all PGN files
    nPlayers: int
        The number of players to show in the plot
    useCurrentHighestRanking: bool
        If this is ture, the players will be chosen to be the highest ranked after each round, not at the end of the tournament
    """
    plotData = list()
    for pgnPath in pgnPaths:
        tournamentResults = list()
        roundResults = getRoundByRoundResults(pgnPath)
        playerResults = getPlayerResults(pgnPath)
        rankings = getPlayerRankings(playerResults)
        if useCurrentHighestRanking:
            totalPoints = dict()
            for player in roundResults.keys():
                totalPoints[player] = [sum(roundResults[player][:i]) for i in range(1, len(roundResults[player])+1)]
            tournamentResults.append(totalPoints[rankings[0]])
            for j in range(nPlayers-1):
                tournamentResults.append(list())
            for i in range(len(roundResults[rankings[0]])):
                bestRoundPoints = list(reversed(sorted([totalPoints[player][i] for player in rankings[1:]])))
                for j in range(nPlayers-1):
                    tournamentResults[j+1].append(bestRoundPoints[j])
        else:
            for player in rankings[:nPlayers]:
                tournamentResults.append([sum(roundResults[player][:i]) for i in range(1, len(roundResults[player])+1)])
        plotData.append(tournamentResults)

    avgData = list()
    for i in range(nPlayers):
        avgData.append([sum([d[i][j] for d in plotData])/len(plotData) for j in range(len(plotData[0][i]))])

    xValues = [list(range(1, len(avgData[0])+1))] * nPlayers
    plotting_helper.plotLineChart(xValues, avgData, 'Round', 'Points', 'Average points after each round for the top 3 players', ['Winner', 'Second place', 'Third place'], linewidth=3, filename=filename)


def plotWinsDrawsLossesByRankings(pgnPaths: list, totalPlayers: int = 8, nRounds: int = 14, filename: str = None):
    plotData = list()
    for i in range(totalPlayers):
        plotData.append([[0, 0], [0, 0], [0, 0]])
    for pgnPath in pgnPaths:
        playerResults = getPlayerResults(pgnPath)
        rankings = getPlayerRankings(playerResults)
        for i, player in enumerate(rankings):
            plotData[i][0][0] += sum([1 for value in playerResults[player].values() for result in value if result[0] == 1 and result[1]])
            plotData[i][0][1] += sum([1 for value in playerResults[player].values() for result in value if result[0] == 1 and not result[1]])
            plotData[i][1][0] += sum([1 for value in playerResults[player].values() for result in value if result[0] == 0.5 and result[1]])
            plotData[i][1][1] += sum([1 for value in playerResults[player].values() for result in value if result[0] == 0.5 and not result[1]])
            plotData[i][2][0] += sum([1 for value in playerResults[player].values() for result in value if result[0] == 0 and result[1]])
            plotData[i][2][1] += sum([1 for value in playerResults[player].values() for result in value if result[0] == 0 and not result[1]])

    colors = plotting_helper.getColors(['slightly better', 'much better', 'yellow', 'darkorange', 'red', 'darkred'])
    legend = ['White wins', 'Black wins', 'White draws', 'Black draws', 'White losses', 'Black losses']
    width = 0.25
    offset = width * -1
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    for bar in range(3):
        white = [data[bar][0]/(nRounds * len(pgnPaths)) for data in plotData]
        black = [data[bar][1]/(nRounds * len(pgnPaths)) for data in plotData]
        xValues = [i+1+offset+(width*bar) for i in range(totalPlayers)]
        ax.bar(xValues, white, color=colors[2*bar], width=width, edgecolor='black', linewidth=0.5, label=legend[2*bar])
        ax.bar(xValues, black, color=colors[2*bar+1], bottom=white, width=width, edgecolor='black', linewidth=0.5, label=legend[2*bar+1])

    plt.title('Relative number of wins, draws and losses based on the final standings')
    ax.set_xlabel('Final ranking in the tournament')
    ax.set_ylabel('Relative number of games')
    ax.set_xlim(1+2*offset, totalPlayers-2*offset)
    fig.subplots_adjust(bottom=0.15, top=0.95, left=0.1, right=0.95)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=6)

    if filename:
        plt.savefig(filename, dpi=300)
    else:
        plt.show()


def plotAverageAccuraciesByRanking(pgnPaths: list):
    plotData = list()
    for pgnPath in pgnPaths:
        playerResults = getPlayerResults(pgnPath)
        rankings = getPlayerRankings(playerResults)
        accuracies = getPlayerAccuracies(pgnPath)
        if not plotData:
            for player in rankings:
                plotData.append([accuracies[player][0]/len(pgnPaths), accuracies[player][1]/len(pgnPaths)])
        else:
            for i, player in enumerate(rankings):
                plotData[i][0] += accuracies[player][0]/len(pgnPaths)
                plotData[i][1] += accuracies[player][1]/len(pgnPaths)
        
    plotting_helper.plotPlayerBarChart(plotData, [i+1 for i in range(len(plotData))], 'Accuracy', 'Accuracy based on finishing position', ['Player accuracy', 'Opponent accuracy'])


def plotOpportunitiesByRanking(pgnPaths: list, filename: str = None):
    rawData = list()
    for pgnPath in pgnPaths:
        playerResults = getPlayerResults(pgnPath)
        rankings = getPlayerRankings(playerResults)
        opportunities = getPlayerOpportunities(pgnPath)
        if not rawData:
            for player in rankings:
                rawData.append(opportunities[player])
        else:
            for rank, player in enumerate(rankings):
                opp = opportunities[player]
                for j in range(len(opp)):
                    for k in range(len(opp[j])):
                        rawData[rank][j][k] += opp[j][k]
    
    plotData = list()
    for data in rawData:
        plotData.append([data[0][1], data[0][2], data[1][1], data[1][2]])
        for i in range(len(plotData[-1])):
            plotData[-1][i] /= len(pgnPaths)

    colors = plotting_helper.getColors(['blue', 'green', 'orange', 'red'])

    plotting_helper.plotPlayerBarChart(plotData, [i+1 for i in range(len(plotData))], 'Number of games', 'Number of chances', ['Better games', 'Won games', 'Worse games', 'Lost games'], loc='upper center', ncol=4, filename=filename, colors=colors, xLabel='Finishing position')


def plotGameResultsPerRound(pgnPaths: list, nRounds: int = 14, nGames: int = 4, filename: str = None):
    plotData = list()
    for i in range(nRounds):
        plotData.append([0, 0, 0])

    for pgnPath in pgnPaths:
        results = getGameResultsPerRound(pgnPath)
        for i, r in enumerate(results):
            for j in range(len(r)):
                plotData[i][j] += r[j] / (len(pgnPaths) * nGames)

    plotting_helper.plotPlayerBarChart(plotData, [i+1 for i in range(nRounds)], 'Number of games', 'Number of white wins, draws and black wins per round', ['White wins', 'Draws', 'Black wins'], xlabel='Round number', colors=['#ffffff', plotting_helper.getColor('orange'), 'black'], filename=filename)


def plotSharpnessChangeByRanking(pgnPaths: list, nPlayers: int = 8):
    allData = list()
    for i in range(nPlayers):
        allData.append(list())

    for pgnPath in pgnPaths:
        playerResults = getPlayerResults(pgnPath)
        rankings = getPlayerRankings(playerResults)
        sharpChange = getPlayerSharpnessChange(pgnPath)

        for i, player in enumerate(rankings):
            allData[i].extend(sharpChange[player])

    plotData = [[sum(d)/len(d)] for d in allData]

    plotting_helper.plotPlayerBarChart(plotData, [i+1 for i in range(nPlayers)], 'Avg sharpness change per move', 'Sharpness change per move', ['Sharp change'], colors=plotting_helper.getColors(['red']))


if __name__ == '__main__':
    year = 2024
    can = f'../out/candidates{year}_analysed.pgn'
    allCandidates = ['../out/candidates2013_analysed.pgn', '../out/candidates2014_analysed.pgn', '../out/candidates2016_analysed.pgn', '../out/candidates2018_analysed.pgn', '../out/candidates2020_analysed.pgn', '../out/candidates2022_analysed.pgn', '../out/candidates2024_analysed.pgn']
    years = [2013, 2014, 2016, 2018, 2020, 2022, 2024]
    outFolder = '../out/candidatesPlots'
    # print(getPlayerAccuracies(can))
    # plotAverageAccuraciesByRanking(allCandidates)
    # results = getPlayerResults(can)
    # print(getPlayerRankings(results))
    # opps = getPlayerOpportunities(can)
    # plotPointsScoredAgainstSeeds(allCandidates, years, useFinalRankings=True)
    # plotRoundByRoundScores(allCandidates, filename=f'{outFolder}/roundScores.png')
    # plotWinsDrawsLossesByRankings(allCandidates, filename=f'{outFolder}/rankingsWDL.png')
    plotOpportunitiesByRanking(allCandidates)
    # plotGameResultsPerRound(allCandidates, filename=f'{outFolder}/roundResults.png')
    # plotSharpnessChangeByRanking(allCandidates)
