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
    columns = ["Position", "Move", "WhiteElo", "BlackElo", "EvalBefore", "EvalAfter", "WinPBefore", "DrawPBefore", "LossPBefore", "WinPAfter", "DrawPAfter", "LossPAfter", "Result"]
    data = dict()
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
    df = pd.DataFrame(data)
    return df


if __name__ == '__main__':
    pgns = ['../out/games/2700games2023-out.pgn']
    df = readMoveData(pgns)
    print(df)
