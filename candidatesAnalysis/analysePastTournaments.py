import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


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
                accuracies[white] = [0, 0]
            if black not in accuracies:
                accuracies[black] = [0, 0]

            node = game
            cpB = None

            while not node.is_end():
                node = node.variations[0]

                if not functions.readComment(node, True, True):
                    continue
                cpA = functions.readComment(node, True, True)[1]

                if cpB is not None:
                    if node.turn():
                        factor = -1
                        player = black
                    else:
                        factor = 1
                        player = white
                    xsB = functions.expectedScore(cpB * factor)
                    xsA = functions.expectedScore(cpA * factor)
                    acc = functions.accuracy(xsB, xsA)
                    accuracies[player][0] += acc
                    accuracies[player][1] += 1
                cpB = cpA

    avgAcc = dict()
    for player, accData in accuracies.items():
        avgAcc[player] = round(float(accData[0]/accData[1]), 3)

    return avgAcc


def getPlayerOpportunities(pgnPath: str) -> dict:
    """
    This function counts how often players got opportunities with a better position during the tournament
    return -> dict:
        {playerNames: [[totalOpp, gamesWithOpp, wonGames], [opponentTotalOpp, gamesWithOpponentOpp, lostGames]], ...}
    """
    opportunities = dict()
    cpThreshold = 150

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

                if -cpThreshold < cpEval < cpThreshold:
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


if __name__ == '__main__':
    year = 2024
    can = f'../out/candidates{year}_analysed.pgn'
    print(getPlayerAccuracies(can))
    results = getPlayerResults(can)
    print(getPlayerRankings(results))
    opps = getPlayerOpportunities(can)
    for player, o in opps.items():
        print(player, o)
