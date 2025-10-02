import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import pandas as pd


def extractMoveData(pgnPaths: list) -> pd.DataFrame:
    data = dict()
    keys = ['Rating', 'Time', 'EvalBefore', 'EvalAfter', 'MoveNr']
    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                wElo = game.headers['WhiteElo']
                bElo = game.headers['BlackElo']

                wTime = None
                bTime = None
                lastEval = None

                node = game
                while not node.is_end():
                    white = node.board().turn
                    node = node.variations[0]
