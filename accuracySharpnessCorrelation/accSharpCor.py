import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import chess


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

            node = game
            node = node.variations[0]
            while not node.is_end():
                if not functions.readComment(node, True, True):
                    break
                wdl, cpBefore = functions.readComment(node, True, True)
                white = node.turn()
                node = node.variations[0]
                if not (comment := functions.readComment(node, True, True)):
                    break
                cpAfter = comment[1]
                sharpness = functions.sharpnessLC0(wdl)

                if white:
                    winPBefore = functions.winP(cpBefore)
                    winPAfter = functions.winP(cpAfter)
                    accuracy = functions.accuracy(winPBefore, winPAfter)
                    accSharp[w].append((accuracy, sharpness))
                else:
                    winPBefore = functions.winP(-1 * cpBefore)
                    winPAfter = functions.winP(-1 * cpAfter)
                    accuracy = functions.accuracy(winPBefore, winPAfter)
                    accSharp[b].append((accuracy, sharpness))
    return accSharp


if __name__ == '__main__':
    pgn = '../out/wijkMasters2024-5000-30.pgn'
    print(accSharpPerPlayer(pgn))
