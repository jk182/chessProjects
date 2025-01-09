import chess
from chess import pgn
import pandas as pd
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


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

    whiteWins = df[(df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1-0")]
    blackWins = df[(df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "0-1")]
    whiteDraws = df[(df["EvalAfter"] >= cpCutoff) & (df["Result"] == "1/2-1/2")]
    blackDraws = df[(df["EvalAfter"] <= -cpCutoff) & (df["Result"] == "1/2-1/2")]
    whiteGames = df[df["EvalAfter"] >= cpCutoff]
    blackGames = df[df["EvalAfter"] <= -cpCutoff]

    nWins = len(set(wins["GameID"]))
    nDraws = len(set(draws["GameID"]))
    nGames = len(set(games["GameID"]))

    nWhiteWins = len(set(whiteWins["GameID"]))
    nBlackWins = len(set(blackWins["GameID"]))
    nWhiteDraws = len(set(whiteDraws["GameID"]))
    nBlackDraws = len(set(blackDraws["GameID"]))
    nWhiteGames = len(set(whiteGames["GameID"]))
    nBlackGames = len(set(blackGames["GameID"]))
    return ((nWhiteWins + 0.5*nWhiteDraws)/nWhiteGames, (nBlackWins + 0.5*nBlackDraws)/nBlackGames)
    # return (nWins + 0.5*nDraws)/nGames


if __name__ == '__main__':
    pgns = ['../out/games/2700games2023-out.pgn']
    df = readMoveData(pgns)
    df26 = filterGamesByRating(df, (2600, 2700), 100)
    df27 = filterGamesByRating(df, (2700, 2900), 100)
    for cp in [0, 50, 100, 150, 200, 250, 300, 400, 500]:
        prob = getExpectedScore(df, cp)
        print(cp)
        print(prob)
        print((prob[0]+prob[1])/2)
