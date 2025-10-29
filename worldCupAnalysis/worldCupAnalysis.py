import chess
import chess.pgn
import pandas as pd

from os import listdir
from os.path import isfile, join


def extractData(pgnPaths: list) -> pd.DataFrame:
    data = dict()
    keys = ["Match", "Round", "GameNr", "White", "Black", "WhiteElo", "BlackElo", "Result"]

    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        print(pgnPath)
        year = pgnPath[-6:-4]
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
                data["Result"].append(header["Result"])
    return pd.DataFrame.from_dict(data)


if __name__ == '__main__':
    worldCups = '../resources/worldCups/'
    pgns = [join(worldCups, f) for f in listdir(worldCups) if isfile(join(worldCups, f))]
    df = extractData(pgns)
    print(list(df["Round"]))
