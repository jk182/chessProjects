import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
from pieceActivity import pieceActivity as pa
from pieceHeatmaps import pieceHeatmaps as heatmap
from chess import engine, pgn, Board
import chess
import matplotlib.pyplot as plt
import numpy as np


def genFigure(figsize: tuple = (10,6), title: str = "", xLabel: str = "", yLabel: str = "") -> tuple:
    """
    Wrapper to generate subplots
    """
    fig, ax = plt.subplots(figsize=figsize)

    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    plt.title(title)
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    return (fig, ax)


def getComments(pgnPath: str) -> list:
    """
    This function reads the comments from a PGN file and returns them as a list containing a tuple with the WDL and CP score.
    Each list entry is one game
    """
    scores = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            curScores = list()
            node = game
            while not node.is_end():
                node = node.variations[0]
                curScores.append(functions.readComment(node, True, True))

            scores.append(curScores)

    return scores


def plotWDL(scores: list, filename: str = None):
    """
    Plots a WDL graph given the scores from a game
    """
    colors = ['#FDFDFD', '#e6f7f2', '#040404']
    wdls = [ s[0] for s in scores ]
    w = [ wdl[0]/1000 for wdl in wdls ]
    d = [ wdl[1]/1000 for wdl in wdls ]
    l = [ wdl[2]/1000 for wdl in wdls ]

    fig, ax = genFigure(title="WDL Plot", xLabel="Move Number", yLabel="Win Probability")
    plt.xlim(0, len(wdls)-1)
    ax.set_xticks([i for i in range(0, len(wdls), 20)])
    ax.set_xticklabels([i//2 for i in range(0, len(wdls), 20)])
    plt.ylim(0,1)
    ax.stackplot(range(len(wdls)), np.vstack([w, d, l]), colors=colors, edgecolor='grey')

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def sharpChangeByColor(scores: list) -> dict:
    """
    This function calculates the sharpness change per move for each color in a list of PGN files.
    scores: list
        The scores from the game
    return -> dict
        A dictionary indexed by color and containing a list of tuples containing the sharpness change and the move number
    """
    startSharp = 0.468*0.5
    lastSharp = startSharp

    sharp = {'white': list(), 'black': list()}
    for ply, (wdl, cp) in enumerate(scores):
        curSharp = functions.sharpnessLC0(wdl) * ((1000-max(wdl))/1000) # Rescaled sharpness to prevent high values for winning positions
        diff = max(-3, min(3, float(curSharp-lastSharp))) # max, min to prevent huge swings
        lastSharp = curSharp
        
        if ply % 2 == 0:
            sharp['white'].append(diff)
        else:
            sharp['black'].append(diff)

    return sharp


def plotSharpnessChange(scores: list, filename: str = None):
    """
    This function plots the sharpness change for a game with the scores given
    """
    sharpChange = sharpChangeByColor(scores)
    white = sharpChange['white']
    black = sharpChange['black']

    fig, ax = genFigure(title='Sharpness Change', xLabel='Move Number', yLabel='Sharpness Change')
    ax.plot(range(1, len(white)+1), white, color='#f8a978', label='White sharpness change')
    ax.plot(range(1, len(black)+1), black, color='#111111', label='Black sharpness change')
    plt.axhline(0, color='black', linewidth=0.5)
    ax.set_xlim(1, len(white)+1)
    ax.legend()

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getInaccMistakesBlunders(scores: list) -> dict:
    """
    This function calculates the number of inaccuracies, mistakes and blunders given the CP scores
    scores: list
        The CP scores of a game
    return -> dict
        Dictionary indexed by color, containing a list [inaccuracies, mistakes, blunders]
    """
    imb = {'white': [0, 0, 0], 'black': [0, 0, 0]}
    cutOffs = (10, 15, 20)
    lastWP = None

    for ply, (wdl, cp) in enumerate(scores):
        winP = functions.winP(cp)
        if not lastWP:
            lastWP = winP
            continue

        if ply % 2 == 0:
            diff = lastWP - winP
            for i in range(len(cutOffs)):
                j = len(cutOffs) - i - 1
                if diff >= cutOffs[j]:
                    imb['white'][j] += 1
                    break
        else:
            diff = (100-lastWP) - (100-winP)
            for i in range(len(cutOffs)):
                j = len(cutOffs) - i - 1
                if diff >= cutOffs[j]:
                    imb['black'][j] += 1
                    break

        lastWP = winP
    return imb


def getMoveAccuracies(scores: list) -> dict:
    """
    This function calculates the move accuracies given the scores of a game
    scores: list
        The CP scores from a game
    return -> dict
        Dictionary index by color with the move accuracies
    """
    accuracies = {'white': list(), 'black': list()}
    lastWP = None

    for ply, (wdl, cp) in enumerate(scores):
        winP = functions.winP(cp)
        if not lastWP:
            lastWP = winP
            continue

        if ply % 2 == 0:
            accuracies['white'].append(functions.accuracy(lastWP, winP))
        else:
            accuracies['black'].append(functions.accuracy(100-lastWP, 100-winP))
        lastWP = winP

    return accuracies


def getClockTimes(pgnPath: str) -> dict:
    """
    This function gets the clocktimes for each move for Black and White
    pgnPath: str
        Path to the PGN file which contains the clock times
    return -> dict
        A dictionary indexed by color and containing a list with the clocktimes
    """
    clock = {'white': list(), 'black': list()}
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            node = game
            while not node.is_end():
                node = node.variations[0]
                time = int(node.clock())
                if not time:
                    break

                if not node.turn():
                    clock['white'].append(time)
                else:
                    clock['black'].append(time)
            # TODO
            break
    return clock


def plotLineGraph(data: dict(), yLabel: str, labels: list, title: str, filename: str = None):
    """
    This plots a line graph for both colors where the number of moves are on the x-axis
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Move number')
    ax.set_ylabel(yLabel)
    plt.title(title)
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    
    white = data['white']
    black = data['black']

    ax.plot(range(1, len(white)+1), white, color='#f8a978', label=labels[0])
    ax.plot(range(1, len(black)+1), black, color='#111111', label=labels[1])
    plt.axhline(0, color='black', linewidth=0.5)
    ax.set_xlim(1, len(white)+1)
    ax.legend()

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def generateGameReport(pgnPath: str, filename: str = None):
    """
    This function generates a game report for the given PGN file
    pgnPath: str
        The path to the PGN file
    filename: str
        Template for the filenames of the graphs. If no name is given, the graphs will be shown instead of saved.
    """
    comments = getComments(pgnPath)
    for c in comments:
        if filename:
            plotWDL(c, filename=f'{filename}WDL.png')
            plotSharpnessChange(c, filename=f'{filename}Sharp.png')
            pa.plotPieceActivity(pgnPath, filename=f'{filename}Activity.png')
        else:
            plotWDL(c)
            plotSharpnessChange(c)
            pa.plotPieceActivity(pgnPath)


if __name__ == '__main__':
    # generateGameReport('../out/games/ding-gukesh-out.pgn')
    clocks = getClockTimes('../resources/ding-gukesh-clocks.pgn')
    print(clocks)
    plotLineGraph(clocks, 'Remaining time', ['White time', 'Black time'], 'Clock time')
    """
    pgn = '../out/games/greatGames.pgn'
    gamePGN = '../out/games/carlsenNepo.pgn'
    comments = getComments(pgn)
    carlsenNepo = comments[1]

    print(getInaccMistakesBlunders(carlsenNepo))
    for side, acc in getMoveAccuracies(carlsenNepo).items():
        print(sum(acc)/len(acc))
    plotWDL(carlsenNepo, filename='../out/carlsenNepoWDL.png')
    plotSharpnessChange(carlsenNepo, filename='../out/carlsenNepoSharp.png')
    pa.plotPieceActivity(gamePGN, filename='../out/carlsenNepoAct.png')
    heatmapDataW = heatmap.getAllPieceData(gamePGN, chess.WHITE)
    heatmapDataB = heatmap.getAllPieceData(gamePGN, chess.BLACK)
    heatmap.plotPieceHeatmaps(heatmapDataW, chess.WHITE, filename='carlsenNepoHeatW')
    heatmap.plotPieceHeatmaps(heatmapDataB, chess.BLACK, filename='carlsenNepoHeatB')
    """
