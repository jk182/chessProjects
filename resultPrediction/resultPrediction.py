import chess
import chess.pgn
import pandas as pd
import matplotlib.pyplot as plt
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotting_helper


def extractResultData(pgnPath: str) -> pd.DataFrame:
    keys = ['White', 'Black', 'WhiteElo', 'BlackElo', 'Date', 'Event', 'Result']
    data = dict()
    for key in keys:
        data[key] = list()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            for key in keys:
                if key in game.headers.keys():
                    if 'Elo' in key:
                        data[key].append(int(game.headers[key]))
                    else:
                        data[key].append(game.headers[key])
                else:
                    data[key].append(None)

    df = pd.DataFrame(data)
    return df


def getResultsByRating(df: pd.DataFrame, rating: int, white: bool, offset: int = 10) -> dict:
    """
    This function gets the result for the given rating against all other ratings
    df: pd.DataFrame
        The data extracted by extractResultData
    rating: int
        The rating of the players to look at
    white: bool
        If the games are from White's or Black's perspective
    offset: int
        Offset for a range of ratings
    """
    data = dict()
    if white:
        color = 'White'
        oppColor = 'Black'
    else:
        color = 'Black'
        oppColor = 'White'
    
    for i, row in df.iterrows():
        if row['WhiteElo'] is None or row['BlackElo'] is None:
            continue
        if rating-offset <= row[f'{color}Elo'] <= rating+offset:
            r = row['Result']
            if r == '1-0':
                rIndex = 0
            elif r == '1/2-1/2':
                rIndex = 1
            elif r == '0-1':
                rIndex = 2
            else:
                continue
            if not white:
                rIndex = 2-rIndex

            oppElo = row[f'{oppColor}Elo']
            if oppElo in data:
                data[oppElo][rIndex] += 1
                data[oppElo][3] += 1
            else:
                data[oppElo] = [0, 0, 0, 1]
                data[oppElo][rIndex] += 1

    avgData = dict()
    for k, v in data.items():
        avgData[k] = [round(v[i]/v[3], 3) for i in range(3)]
    return dict(sorted(avgData.items()))


def plotResultData(data: dict, filename: str = None):
    plotData = dict()
    for k, v in data.items():
        plotData[k] = v[0] + 0.5*v[1]

    plotting_helper.plotScatterPlot(list(plotData.keys()), list(plotData.values()), 'Opponent rating', 'Score', 'Score for 2700 players depending on opponent rating', filename=filename)
    

if __name__ == '__main__':
    pgn = '../resources/2500+gamesUTF8.pgn'
    # df = extractResultData(pgn)
    # print(df)
    # df.to_pickle('../out/all2500games.pkl')
    df = pd.read_pickle('../out/all2500games.pkl')
    white = getResultsByRating(df, 2700, True)
    black = getResultsByRating(df, 2700, False)
    plotResultData(white)
    plotResultData(black)
