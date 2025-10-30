import chess
import chess.pgn
import pandas as pd

import os
from os import listdir
from os.path import isfile, join


def changeRoundNumbers(inFile: str, outFile):
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


def extractData(pgnPaths: list) -> pd.DataFrame:
    data = dict()
    keys = ["Match", "Round", "GameNr", "White", "Black", "WhiteElo", "BlackElo", "WhiteSeed", "BlackSeed", "Result"]

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
        print(seedings)

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
                data["GameNr"].append(int(header["Round"][-1]))
                data["White"].append(header["White"])
                data["Black"].append(header["Black"])
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
    # TODO: can color sequence change in tiebreaks?
    matchData = dict()
    keys = ["Match", "Round", "White", "Black", "WhiteElo", "BlackElo", "GameResults", "MatchResult", "Tiebreak"]

    for i, row in df.iterrows():
        match = row["Match"]
        if match not in matchData.keys():
            matchData[match] = dict()
            matchData[match]["Round"] = row["Round"]
            matchData[match]["GameResults"] = list()
        gameNr = row["GameNr"]
        if gameNr == 1:
            for k in ["White", "Black", "WhiteElo", "BlackElo"]:
                matchData[match][k] = row[k]

        if gameNr <= len(matchData[match]["GameResults"]):
            matchData[match]["GameResults"][gameNr-1] = row["Result"]
        else:
            l = [0] * (gameNr - len(matchData[match]["GameResults"]))
            l[gameNr - len(matchData[match]["GameResults"]) - 1] = row["Result"]
            matchData[match]["GameResults"].extend(l)

    for match in matchData.keys():
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
            if i % 2 == 0 and result == "1-0":
                wPoints += 1
            elif i % 2 == 1 and result == "0-1":
                wPoints += 1
        if wPoints > len(gameResults) / 2:
            matchData[match]["MatchResult"] = "1-0"
        elif wPoints < len(gameResults) / 2:
            matchData[match]["MatchResult"] = "0-1"
        else:
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
    nGames = len(df)
    
    for i, row in df.iterrows():
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


def getWDLAfterFirstGame(df: pd.DataFrame) -> list:
    firstRoundResults = dict()
    for i, row in df.iterrows():
        matchName = row["Match"]
        if row["GameNr"] == 1:
            firstRoundResults[matchName] = row["Result"]

        print(row)


if __name__ == '__main__':
    # changeRoundNumbers('../resources/wcupW23Bad.pgn', '../resources/worldCups/wcupW23.pgn')
    worldCups = '../resources/worldCups/'
    pgns = [join(worldCups, f) for f in listdir(worldCups) if isfile(join(worldCups, f))]
    df = extractData(pgns)
    print(df)
    analyseGameResults(df)
    """
    matchData = getMatchData(df)
    mustWin = mustWinGames(matchData)
    # Looking at results in must win games
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
    # Tiebreaks
    nTiebreaks = 0
    for match in matchData.keys():
        if matchData[match]["Tiebreak"]:
            nTiebreaks += 1
    print(nTiebreaks/len(matchData))
    """
    # print(getWDLAfterFirstGame(df))
