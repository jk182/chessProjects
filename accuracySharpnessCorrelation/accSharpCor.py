import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def accSharpPerPlayer(pgnPath: str) -> dict:
    """
    This function calculates the accuracy and sharpness on each move.
    pgnPath: str
        Path to the PGN file
    return -> dict
        Dictionary indexed by players containing a list of tuples (acc, sharp)
    """
    accSharp = dict()
    with open (pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            if (w := game.headers['White']) not in accSharp.keys():
                accSharp[w] = list()
            if (b := game.headers['Black']) not in accSharp.keys():
                accSharp[b] = list()
