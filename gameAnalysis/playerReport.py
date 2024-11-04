import tournamentReport
import matplotlib.pyplot as plt
import chess
import analysis
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def getPlayerScores(pgnPaths: list, playerName: str) -> list:
    """
    This function gets the scores for an individual player (see tournamentReport.getPlayerScores)
    pgnPaths: list
        The paths to the PGN files
    playerName: str
        The name of the player, as it appears in the PGN file
    return -> list
        A list of the total games, total points, white games, white points, black games, black points for each PGN file
    """
    scores = list()
    for pgnPath in pgnPaths:
        scores.append(tournamentReport.getPlayerScores(pgnPath)[playerName])
    return scores


def plotPlayerScores(scores: list, labels: list, title: str, filename: str = None):
    """
    This function plots the scores of players
    scores: list
        A list of the lists returned by getPlayerScores
    labels: list
        The labels for the chart
    title: str
        The title of the plot
    filename: str
        The name of the file where the plot should be saved to.
        If no name is specified, the plot will be shown instead
    """
    colors = ['#f8a978', '#FFFFFF', '#111111']
    barLabels = ['Total Score', 'Score with White', 'Score with Black']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    plt.xticks(ticks=range(1, len(labels)+1), labels=labels)

    width = 0.8/3
    offset = width * (1/2-3/2)

    for j in range(3):
        ax.bar([i+1+offset+(width*j) for i in range(len(labels))], [score[2*j+1]/score[2*j] for score in scores], color=colors[j], edgecolor='black', width=width, label=barLabels[j])

    ax.legend()
    plt.title(title)
    ax.set_ylabel('Score')
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getBetterWorseGames(pgnPaths: list, playerName: str, worse: bool, relative: bool = True) -> list:
    """
    This function gets the number of games where a player was worse and the number of games they lost (see tournamentReport.worseGames)
    pgnPaths: list
        The paths to the PGN files
    playerName: str
        The name of the player
    worse: bool
        If this is True, the worse and lost games will be used, otherwise the better and won games
    relative: bool
        If this is set, the number of games will be relative to the total number of games
    return -> list
        A list for each PGN with the number of worse games and lost games
    """
    data = list()
    for pgnPath in pgnPaths:
        if worse:
            data.append(tournamentReport.worseGames(pgnPath)[playerName])
        else:
            data.append(tournamentReport.betterGames(pgnPath)[playerName])
        if relative:
            games = 0
            with open(pgnPath, 'r') as pgn:
                while chess.pgn.read_game(pgn):
                    games += 1
            data[-1][0] /= games
            data[-1][1] /= games
    return data


def plotBarChart(data: list, xlabels: list, ylabel: str, title: str, legend: list, colors: list = None, filename: str = None):
    """
    A general function to create bar charts
    data is assumed to be a list of lists
    """
    if not colors:
        colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    plt.xticks(ticks=range(1, len(data)+1), labels=xlabels)
    ax.set_ylabel(ylabel)

    nBars = len(data[0])
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    for j in range(nBars):
        ax.bar([i+1+offset+(width*j) for i in range(len(data))], [d[j] for d in data], color=colors[j%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=legend[j])

    ax.legend()
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getInaccMistakesBlunders(pgnPaths: list, playerName: str, perMoves: int = 40) -> list:
    """
    This function gets the inaccuracies, mistakes and blunders made by a player and normalises them according to the number of moves played.
    pgnPaths: list
        The paths to the PGN files
    playerName: str
        The name of the player
    perMoves: int
        The number of moves for which the mistakes should be calculated
    return -> list:
        A list containin a list for each PGN with [i, m, b]
    """
    imb = list()
    for pgnPath in pgnPaths:
        imb.append(tournamentReport.getInaccMistakesBlunders(pgnPath)[playerName])
        with open(pgnPath, 'r') as pgn:
            moves = 0
            while game := chess.pgn.read_game(pgn):
                moves += len(list(game.mainline_moves()))
        for i in range(len(imb[-1])):
            imb[-1][i] /= (moves/perMoves)
    return imb


def getAvgSharpness(pgnPaths: list) -> list:
    """
    This calculates the average sharpness of all positions in the given PGNs
    pgnPaths: list
        Paths to the PGN files to analyse
    return -> list
        Average sharpnesses of the games
    """
    sharp = list()
    for pgnPath in pgnPaths:
        pgnSharp = list()
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                node = game
                while not node.is_end():
                    node = node.variations[0]
                    if node.comment:
                        wdl = functions.readComment(node, True, True)[0]
                        pgnSharp.append(functions.sharpnessLC0(wdl))
        sharp.append(sum(pgnSharp)/len(pgnSharp))
    return sharp


def getOppRatings(pgnPaths: list, playerName: str) -> list:
    """
    This function calculates the average rating of the opponents in the PGNs
    pgnPaths: list
        The paths to the PGN files
    playerName: str
        The name of the player for whom the opponents rating will be calculated
    return -> list
        The average opponents rating for each PGN
    """
    avgRatings = list()
    for pgnPath in pgnPaths:
        pgnRating = list()
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if playerName == game.headers['White']:
                    pgnRating.append(int(game.headers['BlackElo']))
                elif playerName == game.headers['Black']:
                    pgnRating.append(int(game.headers['WhiteElo']))
        avgRatings.append(sum(pgnRating)/len(pgnRating))
    return avgRatings


if __name__ == '__main__':
    # Ding games
    name = 'Ding Liren'
    xlabels = ['2018-2020', '2020-2023', '2023-2024']
    preCovid = '../out/games/dingPreCovid-out.pgn'
    covid = '../out/games/dingCovid-out.pgn'
    postWC = '../out/games/dingPostWC-out.pgn'
    games = [preCovid, covid, postWC]

    scoreColors = ['#f8a978', '#FFFFFF', '#111111']
    scoreLabels = ['Total Score', 'Score with White', 'Score with Black']
    scores = getPlayerScores(games, name)
    print(scores)
    normalisedScores = list()
    for score in scores:
        normalisedScores.append([score[2*i+1]/score[2*i] for i in range(3)])
    # plotBarChart(normalisedScores, xlabels, 'Score', "Ding's game scores", scoreLabels, colors=scoreColors, filename='../out/dingGames/scores.png')
    # plotPlayerScores(scores, xlabels, "Ding's scores")

    better = getBetterWorseGames(games, name, False)
    # plotBarChart(better, xlabels, 'Relative number of games', 'Relative number of better and won games', ['better games', 'won games'], filename='../out/dingGames/better.png')
    worse = getBetterWorseGames(games, name, True)
    # plotBarChart(worse, xlabels, 'Relative number of games', 'Relative number of worse and lost games', ['worse games', 'lost games'], colors=['#f8a978', '#fa5a5a'], filename='../out/dingGames/worse.png')
    
    # TODO: how to visualise the accuracy distribution best?
    # tournamentReport.plotMultAccDistributions(games, [name, name, name], xlabels)

    imb = getInaccMistakesBlunders(games, name)
    imbColors = ['#689bf2', '#f8a978', '#fa5a5a']
    # plotBarChart(imb, xlabels, 'Relative number of naccuracies, mistakes, blunders per 40 moves', 'Inaccuracies, mistakes, blunders per 40 moves', ['Inaccuracies', 'Mistakes', 'Blunders'], colors=imbColors, filename='../out/dingGames/imb.png')

    sharpChange = list()
    avgSC = list()
    print(getAvgSharpness(games))
    for game in games:
        sharpChange.append(analysis.sharpnessChangePerPlayer(game)[name])
        avgSC.append([sum(sharpChange[-1])/len(sharpChange[-1])])

    # plotBarChart(avgSC, xlabels, 'Average sharpness change per move', 'Average sharpness change per move', ['Avg sharp change'], colors=['#fa5a5a'], filename='../out/dingGames/sharpChange.png')
    print(getOppRatings(games, name))
