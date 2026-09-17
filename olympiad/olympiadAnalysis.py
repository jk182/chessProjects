import chess
import chess.pgn
import polars as pl


def extractGames(pgnPaths: str) -> pl.DataFrame:
    keys = ['Date', 'RoundNr', 'BoardNr', 'WhitePlayer', 'BlackPlayer', 'WhiteTeam', 'BlackTeam', 'WhiteElo', 'BlackElo', 'Result', 'GameDuration']
    data = dict()

    for k in keys:
        data[k] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                roundNr = int(game.headers['Round'].split('.')[0])
                boardNr = ((int(game.headers['Round'].split('.')[1]) - 1) % 4) + 1
                # TODO: calculate correct game duration
                gameDuration = 1

                if 'WhiteTeam' not in game.headers:
                    continue
                gameData = [game.headers['Date'], 
                            roundNr, 
                            boardNr, 
                            game.headers['White'],
                            game.headers['Black'],
                            game.headers['WhiteTeam'], 
                            game.headers['BlackTeam'], 
                            int(game.headers['WhiteElo']),
                            int(game.headers['BlackElo']),
                            game.headers['Result'],
                            gameDuration]

                for i, k in enumerate(keys):
                    data[k].append(gameData[i])

    return pl.DataFrame(data)


def getMatchData(gameData: pl.DataFrame) -> dict:
    matchData = dict()

    for game in gameData.iter_rows(named=True):
        print(game)
        if f'{game["WhiteTeam"]}-{game["BlackTeam"]}' in matchData:
            team1Elo = game["WhiteElo"]
            team2Elo = game["BlackElo"]
            result = game["Result"]
        elif f'{game["BlackTeam"]}-{game["WhiteTeam"]}' in matchData:
            team1Elo = game["BlackElo"]
            team2Elo = game["WhiteElo"]
            result = f'{game["Result"].split("-")[1]}-{game["Result"].split("-")[0]}'
        else:
            match = f'{game["WhiteTeam"]}-{game["BlackTeam"]}'
            matchData[match] = dict()
            matchData[match]["BoardResults"] = [0, 0, 0, 0]
            matchData[match]["MatchResult"] = ""
            matchData[match]["Team1BoardElo"] = [0, 0, 0, 0]
            matchData[match]["Team2BoardElo"] = [0, 0, 0, 0]
            matchData[match]["GameDurations"] = [0, 0, 0, 0]
            matchData[match]["RoundNr"] = game["RoundNr"]

            team1Elo = game["WhiteElo"]
            team2Elo = game["BlackElo"]
            result = game["Result"]

        boardNr = game["BoardNr"] - 1
        matchData[match]["BoardResults"][boardNr] = result
        matchData[match]["Team1BoardElo"][boardNr] = game["WhiteElo"]
        matchData[match]["Team2BoardElo"][boardNr] = game["BlackElo"]
        matchData[match]["GameDurations"][boardNr] = game["GameDuration"]

    for match, d in matchData.items():
        if 0 in d["BoardResults"]:
            continue
        team1Points = sum([0.5 if "/" in r else 0 if r[0] == "0" else 1 for r in d["BoardResults"]])
        team2Points = sum([0.5 if "/" in r else 0 if r[-1] == "0" else 1 for r in d["BoardResults"]])
        matchData[match]["MatchResult"] = f'{team1Points}-{team2Points}'

    return matchData


if __name__ == '__main__':
    pgn = '/Users/julian/Downloads/lichess_broadcast_45th-chess-olympiad-budapest-2024-open-i_wYigbpXq_2024.09.22.pgn'
    data = extractGames([pgn])
    matchData = getMatchData(data)
    print(matchData)
    boardData = [[[0, 0, 0], [0, 0, 0], [0, 0, 0]] for _ in range(4)]
    for match, data in matchData.items():
        if not data["MatchResult"]:
            continue
        if float(data["MatchResult"].split('-')[0]) > 2:
            matchResultIndex = 0
        elif float(data["MatchResult"].split('-')[0]) == 2:
            matchResultIndex = 1
        else:
            matchResultIndex = 2
        for i in range(4):
            if data["BoardResults"][i].split('-')[0] == "1":
                boardResultIndex = 0
            elif data["BoardResults"][i].split('-')[0] == "1/2":
                boardResultIndex = 1
            else:
                boardResultIndex = 2
            boardData[i][boardResultIndex][matchResultIndex] += 1

    for d in boardData:
        print([[round(x[i]/sum(x), 2) for i in range(len(x))] for x in d])

    for board in range(4):
        l = [(d["Team1BoardElo"][board]+d["Team2BoardElo"][board])/2 for d in matchData.values()]
        print(sum(l)/len(l))
