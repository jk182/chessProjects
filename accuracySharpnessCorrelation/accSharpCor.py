import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import chess
import numpy as np
import matplotlib.pyplot as plt


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
                sharpness = min(3, sharpness)
                if sharpness > 0:
                    sharpness = 200 * sharpness/(max(wdl)+1)

                if white:
                    winPBefore = functions.winP(cpBefore)
                    winPAfter = functions.winP(cpAfter)
                    accuracy = functions.accuracy(winPBefore, winPAfter)
                    accuracy = min(100, accuracy)
                    accSharp[w].append((accuracy, sharpness))
                else:
                    winPBefore = functions.winP(-1 * cpBefore)
                    winPAfter = functions.winP(-1 * cpAfter)
                    accuracy = functions.accuracy(winPBefore, winPAfter)
                    accuracy = min(100, accuracy)
                    accSharp[b].append((accuracy, sharpness))
    return accSharp


def plotAccSharp(pgnPath: str, filename: str = None):
    """
    This function plots the accuracy and sharpness of all games in the given PGN file.
    pgnPath: str
        Path to the PGN file
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved.
    """
    accSharp = accSharpPerPlayer(pgnPath)

    colors = ['#689bf2', '#7ed3b2', '#ff87ca', '#beadfa', '#f8a978']

    fig, ax = plt.subplots(figsize=(10,6))
    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Sharpness of position')
    ax.set_ylabel('Accuracy')
    ax.set_xlim(0, max([x[1] for acs in accSharp.values() for x in acs]))
    ax.set_ylim(0, 101)

    for player, acs in accSharp.items():
        ax.scatter([a[1] for a in acs], [a[0] for a in acs], color=colors[0], alpha=0.5)

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Sharpness/Accuracy')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()



if __name__ == '__main__':
    pgn = '../out/candidates+wijk.pgn'
    ASP = accSharpPerPlayer(pgn)
    totalAcc = list()
    totalSharp = list()
    for p in ASP.keys():
        acc = [acs[0] for acs in ASP[p]]
        sharp = [acs[1] for acs in ASP[p]]
        totalAcc += acc
        totalSharp += sharp
        print(p, sum(acc)/len(acc), sum(sharp)/len(sharp))
        print(np.corrcoef(acc, sharp))
    print(np.corrcoef(totalAcc, totalSharp))
    plotAccSharp(pgn)
