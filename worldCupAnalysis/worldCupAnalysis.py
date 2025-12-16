import chess
import chess.pgn
import pandas as pd

import os, sys
from os import listdir
from os.path import isfile, join

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


def changeRoundNumbers(inFile: str, outFile: str):
    """
    This function changes the round number is a PGN file
    """
    if os.path.exists(outFile):
        os.remove(outFile)

    with open(inFile, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            url = game.headers["Site"]
            if "round" in url:
                roundNr = url.split("round")[1][1]
            elif "final" in url:
                roundNr = 8
            else:
                print('No round found')
            if "game" in url:
                gameNr = url.split("game")[1][1]
                tiebreakStart = None
            if "tiebreak" in url:
                if tiebreakStart is None:
                    tiebreakStart = int(game.headers["Round"].split(".")[0])
                gameNr = int(game.headers["Round"].split(".")[0])-tiebreakStart + 3
            # print(game)
            game.headers["Round"] = f"{roundNr}.{gameNr}"
            
            print(game, file=open(outFile, "a+"), end="\n\n")


def changeRoundNumbers2025(inFile: str, outFile: str, roundNr: int, gameNrOffset: int = 0):
    """
    This function changes the round number for PGN files of the 2025 World Cup downloaded from Lichess
    """
    with open(inFile, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            gameNr = int(game.headers["Round"].split(".")[0])
            game.headers["Round"] = f"{roundNr}.{gameNr-gameNrOffset}"
            print(game, file=open(outFile, "a+"), end="\n\n")


def extractData(pgnPaths: list) -> pd.DataFrame:
    data = dict()
    keys = ["Match", "Round", "GameNr", "White", "Black", "WhiteElo", "BlackElo", "WhiteSeed", "BlackSeed", "Result", "Opening"]

    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        playerRatings = dict()
        year = pgnPath[-6:-4]
        
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                for color in ["White", "Black"]:
                    if game.headers[color] not in playerRatings.keys():
                        if f'{color}Elo' in game.headers.keys():
                            elo = int(game.headers[f'{color}Elo'])
                        else:
                            elo = 0
                        playerRatings[game.headers[color]] = elo

        seedings = list(dict(reversed(sorted(playerRatings.items(), key=lambda item: item[1]))).keys())

        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                header = game.headers

                playerNames = list()
                for color in ["White", "Black"]:
                    names = header[color].split(",")[0].split(" ")
                    if len(names[0]) > 2 or len(names) == 1:
                        playerNames.append(names[0])
                    else:
                        playerNames.append(f'{names[0]} {names[1]}')

                playerNames = sorted(playerNames)
                matchName = f'{playerNames[0]}-{playerNames[1]}, {year}'

                data["Match"].append(matchName)
                data["Round"].append(int(header["Round"].split(".")[0]))
                data["GameNr"].append(int(header["Round"].split(".")[-1]))
                data["White"].append(header["White"])
                data["Black"].append(header["Black"])
                if "Opening" in header.keys():
                    data["Opening"].append(header["Opening"])
                else:
                    data["Opening"].append("No Opening")
                if "WhiteElo" in header.keys():
                    data["WhiteElo"].append(int(header["WhiteElo"]))
                else:
                    print(data["White"][-1])
                    data["WhiteElo"].append(0)
                if "BlackElo" in header.keys():
                    data["BlackElo"].append(int(header["BlackElo"]))
                else:
                    print(data["Black"][-1])
                    data["BlackElo"].append(0)

                data["WhiteSeed"].append(seedings.index(header["White"])+1)
                data["BlackSeed"].append(seedings.index(header["Black"])+1)
                data["Result"].append(header["Result"])
        
    return pd.DataFrame.from_dict(data)


def getMatchData(gameData: pd.DataFrame) -> dict:
    """
    This function groups the individual games into matches
    - The White player is the player with white in the first game of the match
    gameData: pd.DataFrame
        The DataFrame created by the extractData method
    """
    matchData = dict()
    keys = ["Match", "Round", "White", "Black", "WhiteElo", "BlackElo", "WhiteSeed", "BlackSeed", "GameResults", "MatchResult", "Tiebreak", "WhitePlayers", "Openings"]

    for i, row in df.iterrows():
        match = row["Match"]
        if match not in matchData.keys():
            matchData[match] = dict()
            matchData[match]["Round"] = row["Round"]
            matchData[match]["GameResults"] = list()
            matchData[match]["WhitePlayers"] = list()
            matchData[match]["Openings"] = list()
        gameNr = row["GameNr"]
        if gameNr == 1:
            for k in ["White", "Black", "WhiteElo", "BlackElo", "WhiteSeed", "BlackSeed"]:
                matchData[match][k] = row[k]

        if gameNr <= len(matchData[match]["GameResults"]):
            matchData[match]["GameResults"][gameNr-1] = row["Result"]
            matchData[match]["WhitePlayers"][gameNr-1] = row["White"]
            matchData[match]["Openings"][gameNr-1] = row["Opening"]
        else:
            l = [0] * (gameNr - len(matchData[match]["GameResults"]))
            l[gameNr - len(matchData[match]["GameResults"]) - 1] = row["Result"]
            matchData[match]["GameResults"].extend(l)

            l2 = [0] * (gameNr - len(matchData[match]["WhitePlayers"]))
            l2[gameNr - len(matchData[match]["WhitePlayers"]) - 1] = row["White"]
            matchData[match]["WhitePlayers"].extend(l2)

            l3 = [0] * (gameNr - len(matchData[match]["Openings"]))
            l3[gameNr - len(matchData[match]["Openings"]) - 1] = row["Opening"]
            matchData[match]["Openings"].extend(l3)

    for match in matchData.keys():
        """
        # deprecated
        for i in range(2, len(matchData[match]["GameResults"]), 2):
            if matchData[match]["WhitePlayers"][i] != matchData[match]["WhitePlayers"][0] and i < len(matchData[match]["GameResults"])-1:
                r = matchData[match]["GameResults"][i]
                matchData[match]["GameResults"][i] = matchData[match]["GameResults"][i+1]
                matchData[match]["GameResults"][i+1] = r
        """

        gameResults = matchData[match]["GameResults"]
        if len(gameResults) > 2: # TODO: some finals were 4 games
            matchData[match]["Tiebreak"] = True
        else:
            matchData[match]["Tiebreak"] = False
        wPoints = 0
        for i, result in enumerate(gameResults):
            if result == "1/2-1/2":
                wPoints += 0.5
                continue
            if matchData[match]["WhitePlayers"][i] == matchData[match]["White"] and result == "1-0":
                wPoints += 1
            elif matchData[match]["WhitePlayers"][i] == matchData[match]["Black"] and result == "0-1":
                wPoints += 1
        if wPoints > len(gameResults) / 2:
            matchData[match]["MatchResult"] = "1-0"
        elif wPoints < len(gameResults) / 2:
            matchData[match]["MatchResult"] = "0-1"
        else:
            matchData[match]["MatchResult"] = "0-1"
            # TODO: add armageddon scoring
            print(f'Tied match? {match} {matchData[match]}')

    return matchData


def mustWinGames(matchData: dict) -> dict:
    """
    This function extracts information about must win classical games
    """
    mustWinData = dict()
    for match in matchData.keys():
        results = matchData[match]["GameResults"]
        if results[0] == "1/2-1/2":
            continue
        mustWinData[match] = dict()
        # Switching colors as the match data goes of the first game
        mustWinData[match]["White"] = matchData[match]["Black"]
        mustWinData[match]["Black"] = matchData[match]["White"]
        mustWinData[match]["WhiteElo"] = matchData[match]["BlackElo"]
        mustWinData[match]["BlackElo"] = matchData[match]["WhiteElo"]

        if results[0] == "1-0":
            mustWinData[match]["Leader"] = "Black"
        else:
            mustWinData[match]["Leader"] = "White"

        if results[1] == results[0]:
            mustWinData[match]["MustWinScore"] = 1
        elif results[1] == "1/2-1/2":
            mustWinData[match]["MustWinScore"] = 0.5
        else:
            mustWinData[match]["MustWinScore"] = 0
    return mustWinData


def getWDL(df: pd.DataFrame) -> list:
    wdl = [0, 0, 0]
    nGames = 0
    
    for i, row in df.iterrows():
        if row["GameNr"] > 2:
            continue
        nGames += 1
        if row["Result"] == "1-0":
            wdl[0] += 1
        elif row["Result"] == "1/2-1/2":
            wdl[1] += 1
        elif row["Result"] == "0-1":
            wdl[2] += 1
        else:
            nGames -= 1
            print(f'Could not parse result: {row["Result"]}')

    return [x/nGames for x in wdl]


def analyseGameResults(df: pd.DataFrame):
    wScore = 0
    bScore = 0

    for i, row in df.iterrows():
        if row["Result"] == "1-0":
            wScore += 1
        elif row["Result"] == "0-1":
            bScore += 1
        else:
            wScore += 0.5
            bScore += 0.5

    print(wScore/(wScore+bScore), bScore/(wScore+bScore))


def getWDLAfterFirstGame(matchData: dict) -> list:
    ratingDiffs = [0, 50, 100, 150, 200]
    results = dict()

    for data in matchData.values():
        r = max(ratingDiffs)
        diff = data["WhiteElo"] - data["BlackElo"]
        for i in range(len(ratingDiffs)-1):
            if ratingDiffs[i] <= abs(diff) < ratingDiffs[i+1]:
                r = ratingDiffs[i]
                break

        if r not in results.keys():
            results[r] = dict()
            for i in range(3):
                results[r][i] = [0, 0, 0]

        if data["GameResults"][0] == "1/2-1/2":
            resultIndex = 1

        if diff >= 0:
            if data["GameResults"][0] == "1-0":
                resultIndex = 0
            elif data["GameResults"][0] == "0-1":
                resultIndex = 2
        else:
            if data["GameResults"][0] == "0-1":
                resultIndex = 0
            elif data["GameResults"][0] == "1-0":
                resultIndex = 2
        
        if data["GameResults"][1] == "1/2-1/2":
            results[r][resultIndex][1] += 1
        elif data["GameResults"][1] == "1-0":
            results[r][resultIndex][0] += 1
        else:
            results[r][resultIndex][2] += 1
    print(results)


def seedingAnalysis(df: pd.DataFrame) -> dict:
    roundData = dict()
    for i, row in df.iterrows():
        year = row["Match"][-2:]
        k = f'20{year} R{row["Round"]}'
        if k not in roundData.keys():
            roundData[k] = set()
        for s in ["WhiteSeed", "BlackSeed"]:
            roundData[k].add(row[s])
    return roundData


def decisiveGamesAndTiebreaksPerRound(matchData: dict):
    games = dict()
    matches = dict()
    mustWin = dict()

    for data in matchData.values():
        roundNr = data["Round"]

        if roundNr not in games.keys():
            games[roundNr] = [0, 0]
        if roundNr not in matches.keys():
            matches[roundNr] = [0, 0]
        if roundNr not in mustWin.keys():
            mustWin[roundNr] = [0, 0]

        games[roundNr][1] += 2
        for r in data["GameResults"][:2]:
            if r != "1/2-1/2":
                games[roundNr][0] += 1

        matches[roundNr][1] += 1
        if data["Tiebreak"]:
            matches[roundNr][0] += 1

        if data["GameResults"][0] in ["1-0", "0-1"]:
            mustWin[roundNr][1] += 1
            if data["GameResults"][0] == data["GameResults"][1]:
                mustWin[roundNr][0] += 1

    games = dict(sorted(games.items()))
    matches = dict(sorted(matches.items()))

    plotData = list()

    for r in games.keys():
        plotData.append([games[r][0]/games[r][1], matches[r][0]/matches[r][1]])
        # print(r)
        # print(f'Decisive games: {games[r][0]/games[r][1]}')
        # print(f'Must win conversion: {mustWin[r][0]/mustWin[r][1]}')
        # print(f'Tiebreak rate: {matches[r][0]/matches[r][1]}')
    plotting_helper.plotPlayerBarChart(plotData, games.keys(), 'Percentage of games/matches', 'Decisive game and match results in different rounds', ['Classical game results', 'Match tiebreaks'])


def resultsByRatingGap(df: pd.DataFrame):
    ratingDiffs = [0, 50, 100, 150, 200, 300]
    matchData = getMatchData(df)
    gameData = dict()
    matchResults = dict()

    for data in matchData.values():
        r = max(ratingDiffs)
        diff = data["WhiteElo"] - data["BlackElo"]
        for i in range(len(ratingDiffs)-1):
            if ratingDiffs[i] <= abs(diff) < ratingDiffs[i+1]:
                r = ratingDiffs[i]
                break

        if r not in gameData.keys():
            gameData[r] = [0, 0, 0]
            matchResults[r] = [0, 0, 0, 0] # classical WDL + tiebreak result

        for i in range(2):
            if data["GameResults"][i] == "1/2-1/2":
                gameData[r][1] += 1
                continue
            if (diff >= 0 and i == 0) or (diff < 0 and i == 1):
                if data["GameResults"][i] == "1-0":
                    gameData[r][0] += 1
                else:
                    gameData[r][2] += 1
            else:
                if data["GameResults"][i] == "0-1":
                    gameData[r][0] += 1
                else:
                    gameData[r][2] += 1

        if data["Tiebreak"]:
            matchResults[r][1] += 1
            if (diff >= 0 and data["MatchResult"] == "1-0") or (diff < 0 and data["MatchResult"] == "0-1"):
                matchResults[r][3] += 1
        else:
            if diff >= 0:
                if data["MatchResult"] == "1-0":
                    matchResults[r][0] += 1
                else:
                    matchResults[r][2] += 1
            else:
                if data["MatchResult"] == "0-1":
                    matchResults[r][0] += 1
                else:
                    matchResults[r][2] += 1

    gameData = dict(sorted(gameData.items()))
    matchResults = dict(sorted(matchResults.items()))
    print(gameData)
    print(matchResults)

    plotData = list()
    for wdl in gameData.values():
        plotData.append([x/sum(wdl) for x in wdl])

    xTicks = ['0-50', '50-100', '100-150', '150-200', '200-300', '300+']
    plotting_helper.plotPlayerBarChart(plotData, xTicks, 'Relative number of games', 'Wins, draws and losses based on rating gap', ['Wins', 'Draws', 'Losses'], xlabel='Elo advantage', colors=plotting_helper.getColors(['green', 'blue', 'orange']), filename='../out/worldCups/gameResults.png')

    plotMatchData = list()
    for data in matchResults.values():
        cm = data[0]+data[1]+data[2]
        plotMatchData.append([x/cm if i < 3 else x/data[1] for i,x in enumerate(data)])
    plotting_helper.plotPlayerBarChart(plotMatchData, xTicks, 'Relative number of matches', 'Match results based on rating gap', ['Classical wins', 'Classical draws', 'Classical losses', 'Tiebreak wins'], xlabel='Elo advantage', colors=plotting_helper.getColors(['green', 'blue', 'orange', 'purple']), filename='../out/worldCups/matchResults.png')


def tiebreakImpact(matchData: dict):
    tiebreaks = dict()
    for match, data in matchData.items():
        if data["Tiebreak"]:
            year = match[-2:]
            k = f'{year}R{data["Round"]}'
            if data["MatchResult"] == "1-0":
                player = data["White"]
            else:
                player = data["Black"]

            if k not in tiebreaks.keys():
                tiebreaks[k] = [player]
            else:
                tiebreaks[k].append(player)

    tiebreakData = list()
    results = ["0-1", "1/2-1/2", "1-0"]
    for match, data in matchData.items():
        k = f'{match[-2:]}R{data["Round"]-1}' # looking at tiebreaks in the previous round
        if k not in tiebreaks.keys():
            continue
        if data["White"] in tiebreaks[k] and data["Black"] in tiebreaks[k]:
            # I only want matches where one player had to play a tiebreak
            continue
        td = dict()
        if data["White"] in tiebreaks[k]:
            td["Player"] = data["White"]
            td["EloDiff"] = data["WhiteElo"]-data["BlackElo"]
            td["GameResults"] = [results.index(data["GameResults"][0])/2, (2-results.index(data["GameResults"][1]))/2]
            td["MatchResult"] = results.index(data["MatchResult"])/2
        elif data["Black"] in tiebreaks[k]:
            td["Player"] = data["Black"]
            td["EloDiff"] = data["BlackElo"]-data["WhiteElo"]
            td["GameResults"] = [(2-results.index(data["GameResults"][0]))/2, results.index(data["GameResults"][1])/2]
            td["MatchResult"] = (2-results.index(data["MatchResult"]))/2
        else:
            continue
        td["Tiebreak"] = data["Tiebreak"]
        tiebreakData.append(td)

    scores = [0, 0]
    matchPoints = 0
    ratingDiff = 0
    ratingDiffs = [0, 50, 100, 200, 300]
    tbGameData = dict()
    tbMatchData = dict()
    for tb in tiebreakData:
        matchPoints += tb["MatchResult"]
        ratingDiff += tb["EloDiff"]
        for i in range(2):
            scores[i] += tb["GameResults"][i]

        r = max(ratingDiffs)
        for i in range(len(ratingDiffs)-1):
            if ratingDiffs[i] <= abs(tb["EloDiff"]) < ratingDiffs[i+1]:
                r = ratingDiffs[i]
                continue
        if tb["EloDiff"] < 0:
            r *= -1
        
        if r not in tbMatchData.keys():
            tbGameData[r] = [[0, 0, 0], [0, 0, 0]]
            tbMatchData[r] = [0, 0, 0, 0]

        for j in range(2):
            tbGameData[r][j][2-int(tb["GameResults"][j]*2)] += 1
        if tb["Tiebreak"]:
            offset = 2
        else:
            offset = 0
        tbMatchData[r][1-int(tb["MatchResult"])+offset] += 1

    tbGameData = dict(sorted(tbGameData.items()))
    tbMatchData = dict(sorted(tbMatchData.items()))
    print([s/len(tiebreakData) for s in scores])
    print(matchPoints/len(tiebreakData))
    print(ratingDiff/len(tiebreakData))
    print(tbGameData)
    print(tbMatchData)
    plotData = [[x/sum(d[0]) for x in d[0]] for d in tbGameData.values()]
    plotData2 = [[x/sum(d[1]) for x in d[1]] for d in tbGameData.values()]
    plotData3 = [[(d[0][0]+d[0][1]*0.5)/sum(d[0]), (d[1][0]+d[1][1]*0.5)/sum(d[1])] for d in tbGameData.values()]
    # plotting_helper.plotPlayerBarChart(plotData, [-200, -100, -50, 0, 50, 100, 200], 'Relative number of games', 'Result after tiebreak', ['Wins', 'Draws', 'Losses'])
    # plotting_helper.plotPlayerBarChart(plotData2, [-200, -100, -50, 0, 50, 100, 200], 'Relative number of games', 'Result after tiebreak game 2', ['Wins', 'Draws', 'Losses'])
    plotting_helper.plotPlayerBarChart(plotData3, [-200, -100, -50, 0, 50, 100, 200], 'Relative number of games', 'Result after tiebreak game 2', ['Wins', 'Draws', 'Losses'])


def mustWinGamesByRating(mustWinData: dict):
    ratings = [0, 50, 100, 200]
    mwData = dict()

    for data in mustWinData.values():
        if data["Leader"] == "White":
            colorIndex = 1
            eloDiff = data["BlackElo"]-data["WhiteElo"]
        else:
            colorIndex = 0
            eloDiff = data["WhiteElo"]-data["BlackElo"]
        
        ratingBucket = 300
        for i in range(len(ratings)-1):
            if ratings[i] <= abs(eloDiff) < ratings[i+1]:
                ratingBucket = ratings[i]
                break
        if eloDiff < 0:
            ratingBucket *= -1

        if ratingBucket not in mwData.keys():
            mwData[ratingBucket] = [[0, 0, 0], [0, 0, 0]] # White and black WDL

        mws = data["MustWinScore"]
        if mws == 1:
            mwData[ratingBucket][colorIndex][0] += 1
        if mws == 0.5:
            mwData[ratingBucket][colorIndex][1] += 1
        else:
            mwData[ratingBucket][colorIndex][2] += 1

    mwData = dict(sorted(mwData.items()))
    plotData = list()
    for data in mwData.values():
        l = list()
        for d in data:
            if sum(d) > 0:
                l.append([x/sum(d) for x in d])
            else:
                l.append([0, 0, 0])

        plotData.append(l)
    print(plotData)
    whiteData = [l[0] for l in plotData]
    blackData = [l[1] for l in plotData]
    # plotting_helper.plotPlayerBarChart(plotData, [-300, -200, -100, -50, 0, 50, 100, 200, 300], 'Relative number of games', 'Results in must win games', ['White wins', 'White draws', 'White losses', 'Black wins', 'Black draws', 'Black losses'])
    colors = plotting_helper.getColors(['green', 'blue', 'orange'])
    plotting_helper.plotPlayerBarChart(whiteData, [-200, -100, -50, 0, 50, 100, 200], 'Relative number of games', 'Results in must win games for White', ['White wins', 'White draws', 'White losses'], xlabel="White's Elo advantage", colors=colors, filename='../out/worldCups/mustWinWhite.png')
    plotting_helper.plotPlayerBarChart(blackData, [-200, -100, -50, 0, 50, 100, 200], 'Relative number of games', 'Results in must win games for Black', ['Black wins', 'Black draws', 'Black losses'], xlabel="Black's elo advantage", colors=colors, filename='../out/worldCups/mustWinBlack.png')


def getUpsetData(matchData: dict):
    upsetData = list()
    results = ["1-0", "1/2-1/2", "0-1"]
    for data in matchData.values():
        upset = dict()
        upset["FirstGame"] = [0, 0, 0]
        upset["SecondGame"] = [0, 0, 0]
        if data["MatchResult"] == "1-0" and data["WhiteElo"]-data["BlackElo"] < -100:
            upset["Tiebreak"] = data["Tiebreak"]
            upset["FirstGame"][results.index(data["GameResults"][0])] += 1
            upset["SecondGame"][2-results.index(data["GameResults"][1])] += 1
            upsetData.append(upset)
        elif data["MatchResult"] == "0-1" and data["BlackElo"]-data["WhiteElo"] < -100:
            upset["Tiebreak"] = data["Tiebreak"]
            upset["FirstGame"][2-results.index(data["GameResults"][0])] += 1
            upset["SecondGame"][results.index(data["GameResults"][1])] += 1
            upsetData.append(upset)

    data = [0, 0, 0]
    for u in upsetData:
        if u["Tiebreak"]:
            data[2] += 1
            continue
        if u["FirstGame"][0] == 1:
            data[0] += 1
        else:
            data[1] += 1
    print([d/sum(data) for d in data])


def plotUpsetsByRound(matchData: dict, rounds: list = None, eloDiff: int = 75, years: list = [2021, 2023, 2025], filename: str = None):
    upsetData = dict()
    if rounds is None:
        rounds = [r+1 for r in range(8)]
    for r in rounds:
        upsetData[r] = [0] * len(years)

    for match, data in matchData.items():
        if int(f'20{match[-2:]}') in years:
            if rounds is not None and data['Round'] not in rounds:
                continue
            if (data["MatchResult"] == "1-0" and data["WhiteElo"]-data["BlackElo"] <= -eloDiff) or (data["MatchResult"] == "0-1" and data["BlackElo"]-data["WhiteElo"] <= -eloDiff):
                print(match, data["Round"], data["MatchResult"], data["WhitePlayers"][0])
                yIndex = years.index(int(f'20{match[-2:]}'))
                upsetData[data["Round"]][yIndex] += 1

    plotData = list()
    for data in upsetData.values():
        plotData.append(list(data))

    plotting_helper.plotPlayerBarChart(plotData, [f'Round {i+1}' for i in range(len(plotData))], 'Number of upsets', 'Number of upsets in the first three rounds in 2021, 2023 and 2025', years, filename=filename)


def setupAxes(ax, maxPlayers=206):
    ax.yaxis.set_major_locator(ticker.NullLocator())
    # ax.xaxis.set_major_locator(ticker.NullLocator())
    ax.spines[['left', 'right', 'top']].set_visible(False)
    ax.set_xlim(0, maxPlayers+1)
    ax.set_ylim(-1, 1)
    ax.set_xticks([1, 25, 50, 75, 100, 125, 150, 175, 200, 206])


def fadeBetweenColors(startColor: tuple, endColor: tuple, steps: int) -> list:
    gradient = list()
    diff = (endColor[0]-startColor[0], endColor[1]-startColor[1], endColor[2]-startColor[2])
    for i in range(steps):
        c = list()
        for j in range(3):
            c.append((startColor[j]+diff[j]*i/steps)/255)
        gradient.append(tuple(c))
    return gradient


def plotPlayerSeeds(df: pd.DataFrame, year: str, nRounds: int = 8, fillUpFirstRound: bool = True, filename: str = None):
    seedingData = seedingAnalysis(df)
    plotData = list()
    for k, v in sorted(seedingData.items()):
        if year in k:
            plotData.append(list(sorted(v)))
            print(len(v), k, sorted(v))

    if fillUpFirstRound:
        maxPlayers = 206
        plotData[0] = list(range(1, maxPlayers+1))

    # all remaining seeds
    gradient = fadeBetweenColors((104, 156, 242), (248, 169, 88), 206)
    gradient = fadeBetweenColors((247, 223, 119), (133, 88, 111), 206)
    gradient = fadeBetweenColors((104, 156, 242), (133, 88, 111), 206)
    fig, ax = plt.subplots(nRounds-1, 1, figsize=(10, 6), layout='constrained')
    fig.suptitle('Remaining seeds before each round')
    fig.patch.set_facecolor(plotting_helper.getColor('background'))
    for i in range(nRounds-1):
        setupAxes(ax[i])
        colors = [gradient[j-1] for j in plotData[i]]
        ax[i].scatter(plotData[i], [0] * len(plotData[i]), s=8, c=colors)
        ax[i].set_facecolor(plotting_helper.getColor('background'))
        ax[i].set_title(f'Round {i+1}')

    # line graph
    """
    plotData = plotData[:-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(plotting_helper.getColor('background'))
    ax.plot(range(1, len(plotData)+1), [max(seed) for seed in plotData], label='Highest seed', color=plotting_helper.getColor('purple'))
    ax.plot(range(1, len(plotData)+1), [min(seed) for seed in plotData], label='Lowest seed', color=plotting_helper.getColor('blue'))
    # ax.plot(range(1, len(plotData)+1), [np.percentile(seed, 25) for seed in plotData], label='Q1')
    ax.plot(range(1, len(plotData)+1), [np.percentile(seed, 50) for seed in plotData], label='Mean seed', color=plotting_helper.getColor('orange'))
    # ax.plot(range(1, len(plotData)+1), [np.percentile(seed, 75) for seed in plotData], label='Q3')
    plt.title('Lowest, mean and highest seed in each round')
    ax.legend()

    ax.set_xlim(1, nRounds-1)
    ax.set_ylim(0.1, 206)
    ax.set_yticks([1, 25, 50, 75, 100, 125, 150, 175, 200, 206])
    ax.set_xlabel('Round')
    ax.set_ylabel('Player seed')
    ax.yaxis.set_inverted(True)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    """
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getAccuracies(pgnPath: str) -> dict:
    mate_score = 10000
    accData = dict()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]
            roundNr = int(game.headers["Round"][0])
            gameNr = int(game.headers["Round"][-1])

            lastEval = None
            xsLosses = [list(), list()]

            node = game
            while not node.is_end():
                node = node.variations[0]
                if node.eval() is None:
                    lastEval = None
                    continue
                currentEval = node.eval().white().score(mate_score = mate_score)

                if lastEval is None:
                    lastEval = currentEval
                    continue

                if not node.turn():
                    xsLoss = max(0, functions.expectedScore(lastEval)-functions.expectedScore(currentEval))
                    xsLosses[0].append(xsLoss)
                else:
                    xsLoss = max(0, functions.expectedScore(-1*lastEval)-functions.expectedScore(-1*currentEval))
                    xsLosses[1].append(xsLoss)

                lastEval = currentEval

            for i, player in enumerate([white, black]):
                if len(xsLosses[i]) == 0:
                    # print(game)
                    xsLoss = (0, 0)
                else:
                    xsLoss = (float(functions.gameAccuracy(float(sum(xsLosses[i])/len(xsLosses[i])))), len(xsLosses[i]))
                if player not in accData.keys():
                    accData[player] = dict()
                if roundNr in accData[player].keys():
                    accData[player][roundNr].append(xsLoss)
                else:
                    accData[player][roundNr] = [xsLoss]
    overallData = dict()
    for player, d in accData.items():
        overallData[player] = list()
        classicalAcc = list()
        rapidAcc = list()
        blitzAcc = list()
        for a in d.values():
            totalAcc = 0
            totalMoves = 0
            for i, x in enumerate(a):
                totalAcc += x[0]*x[1]
                totalMoves += x[1]
                if i == 1:
                    classicalAcc.append((totalAcc, totalMoves))
                    totalAcc = 0
                    totalMoves = 0
                if i == 5:
                    rapidAcc.append((totalAcc, totalMoves))
                    totalAcc = 0
                    totalMoves = 0
                if i == len(a)-1 and i != 5 and totalMoves > 0: 
                    if i < 5:
                        rapidAcc.append((totalAcc, totalMoves))
                    else:
                        blitzAcc.append((totalAcc, totalMoves))
        for tcAcc in [classicalAcc, rapidAcc, blitzAcc]:
            if len(tcAcc) > 0:
                if tcAcc[0][-1] == 0:
                    overallData[player].append(0)
                else:
                    overallData[player].append(sum([b[0] for b in tcAcc])/sum([b[1] for b in tcAcc]))
            else:
                overallData[player].append(0)
    return overallData


def getScoreInBetterAndWorseGames(pgnPath: str, cpCutoff: int = 100) -> dict:
    mate_score = 10000
    data = dict()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]

            for player in [white, black]:
                if player not in data.keys():
                    data[player] = dict()
                    # for each time control, there is a list with the WDL
                    data[player]["better"] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
                    data[player]["worse"] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

            result = game.headers["Result"]
            if result == "1-0":
                resultIndex = 0
            elif result == "1/2-1/2":
                resultIndex = 1
            elif result == "0-1":
                resultIndex = 2
            else:
                print(f'Result {result} not found!')

            gameNr = int(game.headers["Round"][-1])
            if gameNr <= 2:
                tcIndex = 0
            elif gameNr <= 6:
                tcIndex = 1
            else:
                tcIndex = 2
            wBetter = False
            bBetter = False

            node = game
            while not node.is_end():
                node = node.variations[0]
                if node.eval() is None:
                    continue
                cp = node.eval().white().score(mate_score=mate_score)
                if cp > cpCutoff:
                    wBetter = True
                if cp < -cpCutoff:
                    bBetter = True
                if wBetter and bBetter:
                    break
            
            if wBetter:
                data[white]["better"][tcIndex][resultIndex] += 1
                data[black]["worse"][tcIndex][2-resultIndex] += 1
            if bBetter:
                data[white]["worse"][tcIndex][resultIndex] += 1
                data[black]["better"][tcIndex][2-resultIndex] += 1
    return data


def getOpenings(pgnPath: str) -> dict:
    openings = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            opening = game.headers["Opening"].split(':')[0]
            roundNr = int(game.headers["Round"][0])
            white = game.headers["White"]
            black = game.headers["Black"]

            for player in [white, black]:
                if player not in openings.keys():
                    openings[player] = dict()

            if roundNr not in openings[white].keys():
                openings[white][roundNr] = [[opening, None]]
            elif openings[white][roundNr][-1][0] is None:
                openings[white][roundNr][-1][0] = opening
            else:
                openings[white][roundNr].append([opening, None])

            if roundNr not in openings[black].keys():
                openings[black][roundNr] = [[None, opening]]
            elif openings[black][roundNr][-1][1] is None:
                openings[black][roundNr][-1][1] = opening
            else:
                openings[black][roundNr].append([None, opening])
    return openings


def getNumberOfGamesAndMoves(pgnPath: str) -> dict:
    data = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]
            gameNr = int(game.headers["Round"][-1])
            if gameNr <= 2:
                tcIndex = 0
            elif gameNr <= 6:
                tcIndex = 1
            else:
                tcIndex = 2

            for player in [white, black]:
                if player not in data.keys():
                    data[player] = [[0, 0], [0, 0], [0, 0]]
                moves = len(list(game.mainline_moves()))//2
                data[player][tcIndex][0] += 1
                data[player][tcIndex][1] += moves
    return data


def getMustWinResults(matchData: dict) -> dict:
    mustWinData = dict()
    for match, row in matchData.items():
        white = row["White"]
        black = row["Black"]
        for player in [white, black]:
            if player not in mustWinData.keys():
                mustWinData[player] = [[0, 0], [0, 0], [0, 0], [0, 0]] # classical, rapid, blitz, armageddon
        for i, result in enumerate(row["GameResults"]):
            if i == 0:
                tcIndex = 0
            elif i == 2 or i == 4:
                tcIndex = 1
            elif i == 6 or i == 8:
                tcIndex = 2
            elif i == 9:
                mustWinData[row["WhitePlayers"][i]][3][1] += 1
                if result == "1-0":
                    mustWinData[row["WhitePlayers"][i]][3][0] += 1
                break
            else:
                continue
            if result == "1/2-1/2":
                continue
            if result == "1-0":
                if row["WhitePlayers"][i] == white:
                    mwPlayer = black
                else:
                    mwPlayer = white
            else:
                mwPlayer = row["WhitePlayers"][i]
            mustWinData[mwPlayer][tcIndex][1] += 1
            print(row["GameResults"])
            if row["GameResults"][i+1] == result:
                mustWinData[mwPlayer][tcIndex][0] += 1
    return mustWinData


def getPerformanceRatings(matchData: dict) -> dict:
    ratingSums = dict()
    for match, row in matchData.items():
        white = row["White"]
        black = row["Black"]
        wElo = row["WhiteElo"]
        bElo = row["BlackElo"]
        wPoints = [1 if result == "1-0" else 0.5 if result == "1/2-1/2" else 0 for result in row["GameResults"]]

        for player in [white, black]:
            if player not in ratingSums.keys():
                ratingSums[player] = [[0, 0], [0, 0], [0, 0], [0, 0]]

        ratingSums[white][0][0] += bElo
        ratingSums[white][0][1] += 1
        ratingSums[black][0][0] += wElo
        ratingSums[black][0][1] += 1

        for i, wp in enumerate(wPoints):
            if i < 2:
                tcIndex = 1
            elif i < 6:
                tcIndex = 2
            else:
                tcIndex = 3
            
            if row["WhitePlayers"][i] == white:
                whitePoints = wp
                blackPoints = 1-wp
            else:
                whitePoints = 1-wp
                blackPoints = wp
            ratingSums[white][tcIndex][0] += bElo+800*(whitePoints-0.5)
            ratingSums[white][tcIndex][1] += 1
            ratingSums[black][tcIndex][0] += wElo+800*(blackPoints-0.5)
            ratingSums[black][tcIndex][1] += 1
    perfRatings = dict()
    for player, eloData in ratingSums.items():
        perfRatings[player] = list()
        for d in eloData:
            if d[1] > 0:
                perfRatings[player].append(d[0]/d[1])
            else:
                perfRatings[player].append(0)
    return perfRatings


def getPlayerOpenings(matchData: dict) -> dict:
    openings = dict()
    for match, row in matchData.items():
        white = row["White"]
        black = row["Black"]
        roundNr = row["Round"]

        for player in [white, black]:
            if player not in openings.keys():
                openings[player] = dict()
        
        openings[white][roundNr] = [(opening, 'White') if row["WhitePlayers"][i] == white else (opening, "Black") for i, opening in enumerate(row["Openings"])]
        openings[black][roundNr] = [(opening, 'White') if row["WhitePlayers"][i] == black else (opening, "Black") for i, opening in enumerate(row["Openings"])]
    return openings


def plotPlayerCharts(matchData: dict, players: list, pgnPath: str):
    perfRatings = getPerformanceRatings(matchData)
    PRplotData = list()
    for player in players:
        PRplotData.append(perfRatings[player])
    plotting_helper.plotPlayerBarChart(PRplotData, players, 'Rating', 'Opponent and performance rating', ['Avg opponent rating', 'PR classical', 'PR rapid', 'PR blitz'])

    gameAccuracies = getAccuracies(pgnPath)
    accPlotData = list()
    for player in players:
        accPlotData.append(gameAccuracies[player])
    plotting_helper.plotPlayerBarChart(accPlotData, players, 'Accuracy', 'Accuracy in different time controls', ['Classical', 'Rapid', 'Blitz'])


def getOpeningRepeats(matchData: dict):
    openingData = [0, 0]
    for match, data in matchData.items():
        if data["Tiebreak"]:
            openings = [opening.split(':')[0] for opening in data["Openings"]]
            if data["WhitePlayers"][0] == data["WhitePlayers"][2]:
                if openings[0] == openings[2]:
                    openingData[0] += 1
                if openings[1] == openings[3]:
                    openingData[1] += 1
            else:
                if openings[0] == openings[3]:
                    openingData[0] += 1
                if openings[1] == openings[2]:
                    openingData[0] += 1
            openingData[1] += 2
    return openingData


if __name__ == '__main__':
    # changeRoundNumbers('../resources/wcupW23Bad.pgn', '../resources/worldCups/wcupW23.pgn')
    worldCups = '../resources/worldCups/'
    pgns = [join(worldCups, f) for f in listdir(worldCups) if isfile(join(worldCups, f))]
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--round-1_CBWLKDSY_2025.11.03.pgn', '../resources/worldCups/wcup25.pgn', 1)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--round-2_C8xGMEpX_2025.11.06.pgn', '../resources/worldCups/wcup25.pgn', 2, 8)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--round-3_sOK6GBCf_2025.11.09.pgn', '../resources/worldCups/wcup25.pgn', 3, 19)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--round-4_xLyRWYPA_2025.11.13.pgn', '../resources/worldCups/wcup25.pgn', 4, 30)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--round-5_zb9ruNEJ_2025.11.16.pgn', '../resources/worldCups/wcup25.pgn', 5, 41)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--quarterfinals_4Zfj97D4_2025.11.19.pgn', '../resources/worldCups/wcup25.pgn', 6, 49)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--semifinals_25zoKzpI_2025.11.23.pgn', '../resources/worldCups/wcup25.pgn', 7, 55)
    # changeRoundNumbers2025('/Users/julian/Desktop/lichess_broadcast_fide-world-cup-2025--finals_DqmmnYSq_2025.11.26.pgn', '../resources/worldCups/wcup25.pgn', 8, 59)

    outFile = '../out/worldCupData21-25.pkl'
    # df = extractData(['../resources/worldCups/wcup21.pgn', '../resources/worldCups/wcup23.pgn', '../resources/worldCups/wcup25.pgn'])
    # df.to_pickle(outFile)
    # df = pd.read_pickle(outFile)
    df = extractData(['../resources/worldCups/wcup25.pgn'])
    matchData = getMatchData(df)
    print(getOpeningRepeats(matchData))
    # Plots for post about 2025
    """
    """
    # plotPlayerCharts(matchData, ['Yakubboev, Nodirbek', 'Esipenko, Andrey', 'Wei, Yi', 'Sindarov, Javokhir'], '../resources/worldCups/wcup25.pgn')
    # plotUpsetsByRound(matchData, eloDiff=75, filename='../out/wcUpsets.png')
    # plotPlayerSeeds(df, '21')
    # plotPlayerSeeds(df, '23')
    plotPlayerSeeds(df, '25', filename='../out/WCseeds.png')


    """
    for k, v in matchData.items():
        print(k, v)
    mwd = getMustWinResults(matchData)
    for k, v in dict(sorted(mwd.items(), key=lambda x: sum([x[1][i][0] for i in range(len(x[1]))]))).items():
        print(k, v)
    openings = getPlayerOpenings(matchData)
    for k, v in openings.items():
        print(k, v)
    """
    # plotUpsetsByRound(matchData, eloDiff=50)
    # plotUpsetsByRound(matchData, eloDiff=100)
    """
    accuracies = getAccuracies('../resources/worldCups/wcup25.pgn') 
    for i, (k, v) in enumerate(dict(sorted(accuracies.items(), key=lambda item: item[1])).items()):
        print(len(accuracies)-i, k, v)
    """

    """
    for k, v in getScoreInBetterAndWorseGames('../resources/worldCups/wcup25.pgn').items():
        print(k, v)
    for k, v in getOpenings('../resources/worldCups/wcup25.pgn').items():
        print(k, v)
    """
    """
    nMoveData = getNumberOfGamesAndMoves('../resources/worldCups/wcup25.pgn')
    for k, v in dict(sorted(nMoveData.items(), key=lambda x: sum([y[1] for y in x[1]]))).items():
        print(k, v)
    """
    """
    perfRatings = getPerformanceRatings(matchData)
    for k, v in perfRatings.items():
        print(k, v)
    """
    # analyseGameResults(df)
    # Seeding data
    """
    seedingData = seedingAnalysis(df)
    for k, v in sorted(seedingData.items()):
        if '05' in k:
            print(k, v)
        print(k, sorted(v))
    """

    # getUpsetData(matchData)
    # tiebreakImpact(matchData)
    # Having white in the first game
    # resultsByRatingGap(df)
    """
    wWins = 0
    for data in matchData.values():
        if data["MatchResult"] == "1-0":
            wWins += 1
    print(wWins/len(matchData))
    # getWDLAfterFirstGame(matchData)
    # decisiveGamesAndTiebreaksPerRound(matchData)
    """
    # mustWin = mustWinGames(matchData)
    # mustWinGamesByRating(mustWin)
    # Looking at results in must win games
    """
    wdl = [0, 0, 0]
    for match in mustWin.keys():
        if mustWin[match]["MustWinScore"] == 1:
            wdl[0] += 1
        elif mustWin[match]["MustWinScore"] == 0.5:
            wdl[1] += 1
        else:
            wdl[2] += 1
    print([x/sum(wdl) for x in wdl])
    print(getWDL(df))
    """
    """
    # Tiebreaks
    nTiebreaks = 0
    for match in matchData.keys():
        if matchData[match]["Tiebreak"]:
            nTiebreaks += 1
    print(nTiebreaks/len(matchData))
    """
    # print(getWDLAfterFirstGame(df))
