import chess
from chess import pgn
import pandas as pd
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def readMoveData(pgnPaths: list) -> pd.DataFrame:
    """
    This function reads the move data from annotated PGN files and returns a dataframe with data about each move
    """
    startEval = 20
    startWDL = [205, 614, 181]
    columns = ["GameID", "Position", "Move", "WhiteElo", "BlackElo", "EvalBefore", "EvalAfter", "WinPBefore", "DrawPBefore", "LossPBefore", "WinPAfter", "DrawPAfter", "LossPAfter", "Result"]
    data = dict()
    gameID = 0
    for c in columns:
        data[c] = list()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                    print("No Elo")
                    continue
                wElo = int(game.headers["WhiteElo"])
                bElo = int(game.headers["BlackElo"])
                result = game.headers["Result"]
                evalBefore = startEval
                wdlBefore = startWDL

                node = game
                while not node.is_end():
                    board = node.board()
                    node = node.variations[0]
                    if node.comment:
                        data["GameID"].append(gameID)
                        move = node.move
                        data["WhiteElo"].append(wElo)
                        data["BlackElo"].append(bElo)
                        data["Result"].append(result)
                        data["Position"].append(board.fen())
                        data["EvalBefore"].append(evalBefore)
                        data["WinPBefore"].append(wdlBefore[0])
                        data["DrawPBefore"].append(wdlBefore[1])
                        data["LossPBefore"].append(wdlBefore[2])
                        wdl, cp = functions.readComment(node, True, True)
                        data["EvalAfter"].append(cp)
                        data["WinPAfter"].append(wdl[0])
                        data["DrawPAfter"].append(wdl[1])
                        data["LossPAfter"].append(wdl[2])
                        data["Move"].append(move.uci())
                        evalBefore = cp
                        wdlBefore = wdl
                gameID += 1
    df = pd.DataFrame(data)
    return df


def filterGamesByRating(df: pd.DataFrame, ratingRange: tuple, ratingDifference: int) -> pd.DataFrame:
    """
    This filters a dataframe to only include games with the specified rating.
    df: pd.DataFrame
        The dataframe with the move data
    ratingRange: tuple
        Minimum and maximum rating for one of these players
    ratingDifference: int
        The maximal difference in rating between these players
    return -> pd.DataFrame
        Dataframe with only the games where players are in the rating range
    """
    minElo, maxElo = ratingRange
    filtered = df[(abs(df["WhiteElo"]-df["BlackElo"]) <= ratingDifference) & (((minElo <= df["WhiteElo"]) & (df["WhiteElo"] <= maxElo)) | ((minElo <= df["BlackElo"]) & (df["BlackElo"] <= maxElo)))]
    filtered = filtered.reset_index()
    return filtered


def getExpectedScore(df: pd.DataFrame, cpCutoff: int) -> float:
    """
    This calculates the win percentage when one side has an advantage of cpCutoff
    """
    wins = df[((df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1-0")) | ((df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "0-1"))]
    draws = df[(abs(df["EvalAfter"]) >= cpCutoff) & (df["Result"] == "1/2-1/2")]
    games = df[abs(df["EvalAfter"]) >= cpCutoff]

    """
    whiteWins = df[(df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1-0")]
    blackWins = df[(df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "0-1")]
    whiteDraws = df[(df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1/2-1/2")]
    blackDraws = df[(df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "1/2-1/2")]
    whiteGames = df[df["EvalAfter"] >= cpCutoff]
    blackGames = df[df["EvalAfter"] <= -cpCutoff]
    """
    whiteWins = df[(df["EvalAfter"] >= cpCutoff) & (df["EvalAfter"] <= cpCutoff+50) & (df["Result"] == "1-0")]
    blackWins = df[(df["EvalAfter"] <= -cpCutoff) & (df["EvalAfter"] >= -cpCutoff-50) & (df["Result"] == "0-1")]
    whiteDraws = df[(df["EvalAfter"] >= cpCutoff) & (df["EvalAfter"] <= cpCutoff+50) & (df["Result"] == "1/2-1/2")]
    blackDraws = df[(df["EvalAfter"] <= -cpCutoff) & (df["EvalAfter"] >= -cpCutoff-50) & (df["Result"] == "1/2-1/2")]
    whiteGames = df[(df["EvalAfter"] >= cpCutoff) & (df["EvalAfter"] <= cpCutoff+50)]
    blackGames = df[(df["EvalAfter"] <= -cpCutoff) & (df["EvalAfter"] >= -cpCutoff-50)]

    nWins = len(set(wins["GameID"]))
    nDraws = len(set(draws["GameID"]))
    nGames = len(set(games["GameID"]))

    nWhiteWins = len(set(whiteWins["GameID"]))
    nBlackWins = len(set(blackWins["GameID"]))
    nWhiteDraws = len(set(whiteDraws["GameID"]))
    nBlackDraws = len(set(blackDraws["GameID"]))
    nWhiteGames = len(set(whiteGames["GameID"]))
    nBlackGames = len(set(blackGames["GameID"]))
    # return ((nWhiteWins + 0.5*nWhiteDraws)/nWhiteGames, (nBlackWins + 0.5*nBlackDraws)/nBlackGames)
    return ((nWhiteWins + 0.5*nWhiteDraws)+ (nBlackWins + 0.5*nBlackDraws))/(nWhiteGames+nBlackGames)


def winPLichess(cp: int, k: float) -> float:
    """
    This calculates the win percentage with the formula used by Lichess
    """
    return 100/(1+math.exp(-k*cp))


def expectedScore(cp: int, k: float) -> float:
    return 50+100/math.pi * math.atan(k*cp)


def plotExpectedScore(points: list, functions: list, labels: list, title: str, filename: str = None):
    """
    This function plots the given points and functions
    """
    maxEval = 1000
    xRange = [i for i in range(-maxEval-100, maxEval+101)]
    colors = ['#689bf2', '#C3B1E1', '#f8a978', '#fa5a5a', '#5afa8d']
    fig, ax = plt.subplots(figsize=(10,6))
    ax.set_facecolor('#e6f7f2')
    
    xes = [p[0] for p in points]
    ys = [p[1] for p in points]

    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(0, color='black', linewidth=1)
    ax.grid(zorder=0)

    ax.scatter(xes, ys, color=colors[0], label='Avg score in GM games', zorder=3, edgecolor='blue')
    
    for i, (function, parameter) in enumerate(functions):
        ax.plot(xRange, [function(x, parameter) for x in xRange], color=colors[i+1], label=labels[i], linewidth=3)

    ax.legend()
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.xlim(-maxEval*1.05, maxEval*1.05)
    ax.set_xlabel('Centipawn advantage')
    ax.set_ylabel('Expected score')
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.title(title)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()




if __name__ == '__main__':
    pgns = ['../out/games/2700games2023-out.pgn', '../out/games/olympiad2024-out.pgn', '../out/games/grenkeOpen2024.pgn']
    # df = readMoveData(pgns)
    # df.to_pickle('../out/gameDF')
    df = pd.read_pickle('../out/gameDF')
    dfGM = filterGamesByRating(df, (2500, 2900), 50)
    df27 = filterGamesByRating(df, (2700, 2900), 100)
    points = list()
    for cp in [50, 100, 150, 200, 250, 300, 500]:
        prob = getExpectedScore(dfGM, cp)
        print(prob)
        points.append((cp, prob*100))
    plotExpectedScore(points, [(winPLichess, 0.00368208)], ["Lichess win probability"], "Lichess win percentage compared to GM score", filename='../out/lichessWinp.png')
    plotExpectedScore(points, [(winPLichess, 0.00368208), (winPLichess, 0.007545)], ["Lichess win probability", "k=0.007545"], "Updated expected score compared to GM score", filename='../out/newK.png')
    plotExpectedScore(points, [(winPLichess, 0.00368208), (winPLichess, 0.007545), (expectedScore, 0.007851)], ["Lichess win probability", "k=0.007545", "arctan"], "arctan approximation compared to GM score", filename='../out/arctan.png')
