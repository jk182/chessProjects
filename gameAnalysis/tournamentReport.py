# This file produces a report of a tournament given as PGN file
# It uses methods written in analysis.py

import analysis
import chess
import matplotlib.pyplot as plt
import numpy as np


def getPlayers(pgnPath: str, whiteList: list = None) -> list:
    """
    This function gets the names of the players in a tournament.
    pgnPath: str
        The path to the PGN file of the tournament
    whiteList: list
        A list of player names that should be included. The name has to be the same as in the PGN
        If no whiteList is specified, all players will be included
    return -> list
        A list of the players' names
    """
    players = list()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            if (w := game.headers["White"]) not in players:
                if not whiteList:
                    players.append(w)
                else:
                    if w in whiteList:
                        players.append(w)
            if (b := game.headers["Black"]) not in players:
                if not whiteList:
                    players.append(b)
                else:
                    if b in whiteList:
                        players.append(b)
    return players


def generateAccDistributionGraphs(pgnPath: str, players: list):
    """
    This function generates the accuracy distribution graphs for the players in the tournament
    pgnPath: str
        The path to the PGN file of the tournament
    players: list
        A list of the names of the players in the tournament
    """
    for player in players:
        analysis.plotAccuracyDistributionPlayer(pgnPath, player, f'../out/{player}-{pgnPath.split("/")[-1][:-4]}')


def getPlayerScores(pgnPath: str) -> dict:
    """
    This function gets the scores for all players in a tournamet
    pgnPath: str
        The path to the PGN file of the tournament
    return -> dict
        A dictionary indexed by the player containing the number of games, points, games with white, points with white, games with black, points with black
    """
    scores = dict()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            w = game.headers["White"]
            b = game.headers["Black"]
            if w not in scores.keys():
                scores[w] = [0, 0, 0, 0, 0, 0]
            if b not in scores.keys():
                scores[b] = [0, 0, 0, 0, 0, 0]
            scores[w][0] += 1
            scores[w][2] += 1
            scores[b][0] += 1
            scores[b][4] += 1
            if "1/2" in (r := game.headers["Result"]):
                scores[w][1] += 0.5
                scores[w][3] += 0.5
                scores[b][1] += 0.5
                scores[b][5] += 0.5
            elif r == "1-0":
                scores[w][1] += 1
                scores[w][3] += 1
            elif r == "0-1":
                scores[b][1] += 1
                scores[b][5] += 1
            else:
                print(f"Can't identify result: {r}")
    return scores


def getMoveSituation(pgnPath: str) -> dict:
    """
    This function returns a dictionary index by the players and containing the number of moves where they were:
        much better (1+), slightly better (1-0.5), equal, slightly worse and much worse
    """
    moves = dict()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            w = game.headers["White"]
            b = game.headers["Black"]
            if w not in moves.keys():
                moves[w] = [0, 0, 0, 0, 0, 0]
            if b not in moves.keys():
                moves[b] = [0, 0, 0, 0, 0, 0]
            node = game

            while not node.is_end():
                node = node.variations[0]
                if node.comment != 'None' and node.comment:
                    cp = int(float(node.comment.split(';')[-1]))
                    if not node.turn():
                        moves[w][0] += 1
                        if cp > 100:
                            moves[w][1] += 1
                        elif cp >= 50:
                            moves[w][2] += 1
                        elif cp >= -50:
                            moves[w][3] += 1
                        elif cp > -100:
                            moves[w][4] += 1
                        else:
                            moves[w][5] += 1
                    else:
                        moves[b][0] += 1
                        if cp > 100:
                            moves[b][5] += 1
                        elif cp >= 50:
                            moves[b][4] += 1
                        elif cp >= -50:
                            moves[b][3] += 1
                        elif cp > -100:
                            moves[b][2] += 1
                        else:
                            moves[b][1] += 1
    return moves


def worseGames(pgnPath: str) -> dict:
    """
    This function counts the number of games where a player was worse and the number of lost games.
    """
    games = dict()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            w = game.headers["White"]
            b = game.headers["Black"]
            r = game.headers["Result"]
            if w not in games.keys():
                games[w] = [0, 0]
            if b not in games.keys():
                games[b] = [0, 0]
            if r == '1-0':
                games[b][1] += 1
            elif r == '0-1':
                games[w][1] += 1

            node = game
            rec = [False, False]

            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = int(float(node.comment.split(';')[-1]))
                    if cp < -100 and not rec[0]:
                        games[w][0] += 1
                        rec[0] = True
                    elif cp > 100 and not rec[1]:
                        games[b][0] += 1
                        rec[1] = True
    return games


def betterGames(pgnPath: str) -> dict:
    games = dict()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            w = game.headers["White"]
            b = game.headers["Black"]
            r = game.headers["Result"]
            if w not in games.keys():
                games[w] = [0, 0]
            if b not in games.keys():
                games[b] = [0, 0]
            if r == '1-0':
                games[w][1] += 1
            elif r == '0-1':
                games[b][1] += 1

            node = game
            rec = [False, False]

            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = int(float(node.comment.split(';')[-1]))
                    if cp < -100 and not rec[0]:
                        games[b][0] += 1
                        rec[0] = True
                    elif cp > 100 and not rec[1]:
                        games[w][0] += 1
                        rec[1] = True
    return games


def sortPlayers(d: dict, index: int) -> list:
    """
    This function takes a dictionary with a list as values and sorts the keys by the value at the index of the list
    """

    players = list()
    for i in range(len(d.keys())):
        maximum = -1
        for k, v in d.items():
            if k in players:
                continue
            if v[index] > maximum:
                p = k
                maximum = v[index]
        players.append(p)
    return players


def createMovePlot(moves: dict, short: dict = None, filename: str = None):
    """
    This creates a plot with the number of moves a player spent being better or worse
    short: dict
        This is a dict that replaces names that are too long with shorter alternatives
    filename: str
        The name of the file to which the graph should be saved. 
        If no name is specified, the graph will be shown instead of saved
    """
    colors = ['#39b84e', '#6fc97e', '#ECECEC', '#F69E7B', '#EF4B4B']

    fig, ax = plt.subplots()
    ax.set_facecolor('#e6f7f2')
    plt.xticks(rotation=90)

    for player, m in moves.items():
        p = player.split(',')[0]
        if short:
            if p in short.keys():
                p = short[p]
        bottom = 0
        for i in range(len(m)-1, 0, -1):
            ax.bar(p, m[i], bottom=bottom, color=colors[i-1], edgecolor='black', linewidth=0.2)
            bottom += m[i]

    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.1, right=0.95)
    plt.title('Number of moves where players were better, equal and worse')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotScores(scores: dict, short: dict = None, filename: str = None):
    """
    This function plots the scores of the tournament
    filename: str
        The name of the file to which the graph should be saved. 
        If no name is specified, the graph will be shown instead of saved
    """
    sortedPlayers = sortPlayers(scores, 1)
    colors = {3: '#FFFFFF', 5: '#111111'}

    fig, ax = plt.subplots()
    plt.xticks(rotation=90)
    plt.yticks(range(0,10))

    ax.set_facecolor('#e6f7f2')
    for player in sortedPlayers:
        p = player.split(',')[0]
        if short:
            if p in short.keys():
                p = short[p]
        bottom = 0
        for i in [3, 5]:
            ax.bar(p, scores[player][i], bottom=bottom, color=colors[i], edgecolor='black', linewidth=0.7)
            bottom += scores[player][i]

    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.1, right=0.95)
    plt.title('Scores with White and Black')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotWorseGames(worse: dict, short: dict = None, filename: str = None):
    """
    This function plots the number of games in which the players were worse and the number of games they lost
    filename: str
        The name of the file to which the graph should be saved. 
        If no name is specified, the graph will be shown instead of saved
    """
    sort = list(reversed(sortPlayers(worse, 0)))
    labels = list()
    for i, player in enumerate(sort):
        p = player.split(',')[0]
        if short:
            if p in short.keys():
                p = short[p]
        labels.append(p)

    fig, ax = plt.subplots()

    ax.set_facecolor('#e6f7f2')
    plt.xticks(rotation=90)
    plt.yticks(range(0,10))
    plt.xticks(ticks=range(1, len(sort)+1), labels=labels)

    ax.bar([ i+1-0.2 for i in range(len(sort)) ], [ worse[p][0] for p in sort ], color='#689bf2', edgecolor='black', linewidth=0.5, width=0.4, label='# of worse games')
    ax.bar([ i+1+0.2 for i in range(len(sort)) ], [ worse[p][1] for p in sort ], color='#5afa8d', edgecolor='black', linewidth=0.5, width=0.4, label='# of lost games')
    ax.legend()
    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def normaliseAccDistribution(accDis: dict) -> dict:
    """
    This takes an accuracy distribution and normalises the values.
    """
    norm = dict()
    total = sum(accDis.values())
    for k,v in accDis.items():
        norm[k] = v/total
    return norm


def plotMultAccDistributions(pgnPaths: list, filename: str = None):
    """
    This function plots multiple accuracy distribution graphs in one graph
    pgnPaths: list
        The path to the PGN files
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved.
    """
    colors = ['#689bf2', '#f8a978', '#ff87ca', '#beadfa']
    labels = ['Arjun\nClosed', 'Arjun\nOpen']

    fig, ax = plt.subplots()
    ax.set_facecolor('#e6f7f2')
    ax.set_yscale('log')
    plt.xlim(0, 100)
    ax.invert_xaxis()
    for i, pgn in enumerate(pgnPaths):
        # TODO: handle the players
        accDis = analysis.getAccuracyDistributionPlayer(pgn, 'Erigaisi, Arjun')
        accDis = normaliseAccDistribution(accDis)
        ax.bar(accDis.keys(), accDis.values(), width=1, color=colors[i], edgecolor='black', linewidth='0.5', label=labels[i], alpha=0.5)
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Accuracy Distribution')
    ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


if __name__ == '__main__':
    t = '../out/2700games2023-out.pgn'
    nicknames = {'Nepomniachtchi': 'Nepo', 'Praggnanandhaa R': 'Pragg'}
    players = getPlayers(t)
    # generateAccDistributionGraphs(t, players)
    # scores = getPlayerScores(t)
    createMovePlot(getMoveSituation(t), nicknames)
    sharpChange = analysis.sharpnessChangePerPlayer(t)
    analysis.plotSharpChange(sharpChange, short=nicknames)
    # plotScores(scores, nicknames)
    worse = worseGames(t)
    plotWorseGames(worse, nicknames)
    # plotWorseGames(betterGames(t), nicknames)

    """
    arjunC = '../out/arjun_closed.pgn'
    arjunO = '../out/arjun_open-5000-30.pgn'
    name = 'Erigaisi, Arjun'
    WL = [name]
    p2 = getPlayers(arjunC, WL)
    sharpC = analysis.sharpnessChangePerPlayer(arjunC)
    sharpO = analysis.sharpnessChangePerPlayer(arjunO)

    sharpChange = {f'{name}\nClosed': sharpC[name], f'{name}\nOpen': sharpO[name]}
    # analysis.plotSharpChange(sharpChange, filename='../out/sharpArjun.png')
    plotMultAccDistributions([arjunC, arjunO], filename='../out/arjunAccDis.png')
    # generateAccDistributionGraphs(arjunC, p2)
    # generateAccDistributionGraphs(arjunO, p2)
    # analysis.plotSharpChange(analysis.sharpnessChangePerPlayer(arjunC))
    """
