import tournamentReport
import matplotlib.pyplot as plt
import chess
import analysis
import os, sys
import datetime as dt
import pandas as pd

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


def getPlayerRatings(pgnPaths: list, playerName: str) -> dict:
    """
    This function reads the ratings of the specified player in the given PGNs
    pgnPaths: list
        Paths to the PGN files
    playerName: str
        Name of the player
    return -> dict:
        Dictonary indexed by the date and containing the rating at that date as value
    """
    ratings = dict()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                date = game.headers['Date']
                if playerName == game.headers['White']:
                    ratings[date] = int(game.headers['WhiteElo'])
                elif playerName == game.headers['Black']:
                    ratings[date] = int(game.headers['BlackElo'])
    return ratings


def plotPlayerRatings(ratings: dict, oppData: dict, filename: str = None):
    """
    This function plots the ratings of a player given the data from getPlayerRatings and the performance rating
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']

    # Calculate performance Ratings
    perfDates = list()
    perfRatings = list()
    for k, v in oppData.items():
        year = int(k[:4])
        month = int(k[-1])*3 - 1
        day = 15
        perfDates.append(dt.datetime(year, month, day))
        perfRatings.append(v[0]+800*v[1]-400)

    x = [dt.datetime.strptime(d,'%Y.%m.%d').date() for d in ratings.keys()]
    sratings = [d for _, d in sorted(zip(x, ratings.values()))]
    ax.plot(sorted(x), sratings, color=colors[0], label='FIDE rating')
    ax.scatter(perfDates, perfRatings, color=colors[2], label='Performance rating')

    for r in range(2500, 2900, 100):
        plt.axhline(r, color='black', linewidth=1)
    for r in range(2550, 2950, 100):
        plt.axhline(r, color='black', linewidth=0.5)

    plt.xlim(dt.datetime(2019, 1, 1), dt.datetime(2025, 1, 1))
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    ax.legend(loc='upper left')
    ax.set_ylabel('Rating')
    plt.title("Gukesh's rating and performance")
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def getAccuracies(pgnPaths: list, playerName: str) -> list:
    accuracies = list()
    for pgnPath in pgnPaths:
        acc = 0
        moves = 0
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if playerName == game.headers['White']:
                    pTurn = True
                elif playerName == game.headers['Black']:
                    pTurn = False
                else:
                    continue

                node = game
                cpB = None
                
                while not node.is_end():
                    if functions.readComment(node, True, True):
                        sharp = functions.sharpnessLC0(functions.readComment(node, True, True)[0])
                    node = node.variations[0]
                    if not functions.readComment(node, True, True):
                        continue
                    cpA = functions.readComment(node, True, True)[1]
                    if not cpB:
                        cpB = cpA
                        continue

                    if node.turn() != pTurn:
                        if node.turn():
                            wpB = functions.winP(cpB * -1)
                            wpA = functions.winP(cpA * -1)
                        else:
                            wpB = functions.winP(cpB)
                            wpA = functions.winP(cpA)
                        acc += min(100, functions.accuracy(wpB, wpA))
                        moves += 1
        accuracies.append(float(round(acc/moves, 2)))
    return accuracies


def getOpponentDataPerQuarter(pgnPaths: list, playerName: str, cutOff400: bool = False) -> dict:
    """
    This function calculates data from the opponents of the given player and groups it by quarter
    cutOff400: bool
        If this is set, the opponent rating is the maximum of their rating and the player rating - 400 (for performance rating calculations)
    """
    data = dict()
    ratings = dict()
    score = dict()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if playerName == game.headers['White']:
                    rating = int(game.headers['BlackElo'])
                    if cutOff400:
                        rating = max(rating, int(game.headers['WhiteElo'])-400)
                elif playerName == game.headers['Black']:
                    rating = int(game.headers['WhiteElo'])
                    if cutOff400:
                        rating = max(rating, int(game.headers['BlackElo'])-400)
                else:
                    continue
                if '1/2' in (r := game.headers['Result']):
                    s = 0.5
                elif r == '1-0':
                    if playerName == game.headers['White']:
                        s = 1
                    else:
                        s = 0
                elif r == '0-1':
                    if playerName == game.headers['White']:
                        s = 0
                    else:
                        s = 1
                else:
                    continue

                date = dt.datetime.strptime(game.headers['Date'], '%Y.%m.%d').date()
                quarter = pd.Timestamp(date).quarter
                key = f'{date.year}Q{quarter}'
                
                if key in ratings.keys():
                    ratings[key].append(rating)
                else:
                    ratings[key] = [rating]
                
                if key in score.keys():
                    score[key][0] += s
                    score[key][1] += 1
                else:
                    score[key] = [s, 1]

    for k in ratings.keys():
        data[k] = list()
        data[k].append(sum(ratings[k])/len(ratings[k]))
        data[k].append(score[k][0]/score[k][1])
        data[k].append(score[k][1])
    return data


def generatePlayerReport(name: str, pgns: list, xLabels: list, filename: str = None):
    """
    Filename format: directory without file extension (e.g. ../out/gukesh)
    """
    scoreColors = ['#f8a978', '#FFFFFF', '#111111']
    scoreLabels = ['Total Score', 'Score with White', 'Score with Black']
    scores = getPlayerScores(games, name)
    normalisedScores = list()
    for score in scores:
        normalisedScores.append([score[2*i+1]/score[2*i] for i in range(3)])
    better = getBetterWorseGames(games, name, False)
    worse = getBetterWorseGames(games, name, True)

    imbColors = ['#689bf2', '#f8a978', '#fa5a5a']
    imb = getInaccMistakesBlunders(games, name)

    sharpChange = list()
    avgSC = list()
    for game in games:
        sharpChange.append(analysis.sharpnessChangePerPlayer(game)[name])
        avgSC.append([sum(sharpChange[-1])/len(sharpChange[-1])])
    if filename:
        plotBarChart(normalisedScores, xLabels, 'Score', f"{name} game scores", scoreLabels, colors=scoreColors, filename=f'{filename}_scores.png')
        plotBarChart(better, xLabels, 'Relative number of games', 'Relative number of better and won games', ['better games', 'won games'], filename=f'{filename}_better.png')
        plotBarChart(worse, xLabels, 'Relative number of games', 'Relative number of worse and lost games', ['worse games', 'lost games'], colors=['#f8a978', '#fa5a5a'], filename=f'{filename}_worse.png')
        plotBarChart(imb, xLabels, 'Relative number of inaccuracies, mistakes, blunders per 40 moves', 'Inaccuracies, mistakes, blunders per 40 moves', ['Inaccuracies', 'Mistakes', 'Blunders'], colors=imbColors, filename=f'{filename}_imb.png')
        plotBarChart(avgSC, xLabels, 'Average sharpness change per move', 'Average sharpness change per move', ['Avg sharp change'], colors=['#fa5a5a'], filename=f'{filename}_sharp.png')
    else: 
        plotBarChart(normalisedScores, xLabels, 'Score', f"{name} game scores", scoreLabels, colors=scoreColors)
        plotBarChart(better, xLabels, 'Relative number of games', 'Relative number of better and won games', ['better games', 'won games'])
        plotBarChart(worse, xLabels, 'Relative number of games', 'Relative number of worse and lost games', ['worse games', 'lost games'], colors=['#f8a978', '#fa5a5a'])

        plotBarChart(imb, xLabels, 'Relative number of inaccuracies, mistakes, blunders per 40 moves', 'Inaccuracies, mistakes, blunders per 40 moves', ['Inaccuracies', 'Mistakes', 'Blunders'], colors=imbColors)
        plotBarChart(avgSC, xLabels, 'Average sharpness change per move', 'Average sharpness change per move', ['Avg sharp change'], colors=['#fa5a5a'])


if __name__ == '__main__':
    # Ding games
    name = 'Ding Liren'
    xlabels = ['2018-2020', '2020-2023', '2023-2024']
    preCovid = '../out/games/dingPreCovid-out.pgn'
    covid = '../out/games/dingCovid-out.pgn'
    postWC = '../out/games/dingPostWC-out.pgn'
    games = [preCovid, covid, postWC]

    # generatePlayerReport(name, games, xlabels)

    gukesh = 'Gukesh, D'
    xLabels = ['2019', '2020', '2021', '2022', '2023', '2024']
    games = ['../out/games/gukesh2019-out.pgn', '../out/games/gukesh2020-out.pgn', '../out/games/gukesh2021-out.pgn', '../out/games/gukesh2022-out.pgn', '../out/games/gukesh2023-out.pgn', '../out/games/gukesh2024-out.pgn']
    print(getPlayerScores(games, gukesh))
    print(getOppRatings(games, gukesh))
    # generatePlayerReport(gukesh, games, xLabels, '../out/gukesh')
    acc = getAccuracies(games, gukesh)
    # plotBarChart([[a] for a in acc], xLabels, 'Accuracy', "Gukesh's average move accuracy", ['Move Accuracy'], filename='../out/gukesh-accuracy.png')
    ratings = getPlayerRatings(games, gukesh)
    oppData = getOpponentDataPerQuarter(games, gukesh, True)
    plotPlayerRatings(ratings, oppData, filename='../out/gukesh_ratings.png')
