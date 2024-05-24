import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import chess
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def accSharpPerPlayer(pgnPath: str, dbGames: int = None) -> dict:
    """
    This function calculates the accuracy and sharpness on each move.
    pgnPath: str
        Path to the PGN file
    dbGames: int
        The cutoff for book moves.
    return -> dict
        Dictionary indexed by players containing a list of tuples (acc, sharp)
    """
    accSharp = dict()
    with open (pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            nGames = 1000000
            if (w := game.headers['White']) not in accSharp.keys():
                accSharp[w] = list()
            if (b := game.headers['Black']) not in accSharp.keys():
                accSharp[b] = list()

            node = game
            if not node.variations:
                continue
            node = node.variations[0]
            while not node.is_end():
                if not functions.readComment(node, True, True):
                    break
                wdl, cpBefore = functions.readComment(node, True, True)
                white = node.turn()
                oldNode = node
                node = node.variations[0]
                if abs(cpBefore) > 300:
                    continue
                if dbGames:
                    if nGames < dbGames:
                        continue
                    else: 
                        currNGames = functions.getNumberOfGames(node.board().fen())
                        nGames = currNGames
                        if currNGames > dbGames:
                            continue
                if not (comment := functions.readComment(node, True, True)):
                    break
                cpAfter = comment[1]
                sharpness = functions.sharpnessLC0(wdl)
                """
                sharpness = min(3, sharpness)
                if sharpness > 0:
                    sharpness = 200 * sharpness/(max(wdl)+1)
                """
                if white:
                    winPBefore = functions.winP(cpBefore)
                    winPAfter = functions.winP(cpAfter)
                    accuracy = functions.accuracy(winPBefore, winPAfter)
                    # The accuracy is sometimes over 100 but it seems like this only happens when the position gets more winning due to a strong move
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
        ax.scatter([a[1] for a in acs], [a[0] for a in acs], color=colors[2], alpha=0.3)

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Sharpness/Accuracy My Games')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def accuracyPerSharpness(pgns: list, labels: list, maxSharpness: float, intervalls: int, filename: str = None) -> None:
    colors = ['#689bf2', '#ff87ca', '#beadfa', '#7ed3b2', '#f8a978']

    fig, ax = plt.subplots(figsize=(10,6))
    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Sharpness of position')
    ax.set_ylabel('Accuracy')
    ax.set_xticks([i*maxSharpness/intervalls for i in range(intervalls+1)])
    ax.set_xlim(0, maxSharpness)
    for k, pgn in enumerate(pgns):
        acc = list()
        sharp = list()
        ASP = accSharpPerPlayer(pgn)
        for p in ASP.keys():
            acc += [acs[0] for acs in ASP[p]]
            sharp += [acs[1] for acs in ASP[p]]

        accPerSharp = list()
        for i in range(intervalls + 1):
            accPerSharp.append(list())
        for i, s in enumerate(sharp):
            if s >= maxSharpness:
                accPerSharp[intervalls].append(acc[i])
            else:
                accPerSharp[int((s*intervalls)/maxSharpness)].append(acc[i])
        averages = [ sum(aps)/len(aps) for aps in accPerSharp ]
        lengths = [ len(aps) for aps in accPerSharp ]
        print(averages)
        print(lengths)
        x = [ i * maxSharpness / intervalls for i in range(len(averages)) ]

        ax.plot(x, averages, color=colors[k], label=labels[k])

    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    ax.legend()
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


if __name__ == '__main__':
    pgn = '../out/gmGames.pgn'
    pgn2 = '../out/jkClassical-out.pgn'
    accuracyPerSharpness([pgn, pgn2], ['GM games', 'My games'], 2, 10, '../out/accPerS.png')
    ASP = accSharpPerPlayer(pgn)
    totalAcc = list()
    totalSharp = list()
    for p in ASP.keys():
        acc = [acs[0] for acs in ASP[p]]
        sharp = [acs[1] for acs in ASP[p]]
        if not acc or not sharp:
            continue
        totalAcc += acc
        totalSharp += sharp
        print(p, sum(acc)/len(acc), sum(sharp)/len(sharp))
        print(np.corrcoef(acc, sharp))
    print(np.corrcoef(totalAcc, totalSharp))
    print(stats.spearmanr(totalAcc, totalSharp))
    # plotAccSharp(pgn, '../out/gmSharp.png')
    plotAccSharp(pgn2, '../out/jkSharp.png')
