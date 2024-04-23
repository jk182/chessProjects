# This file produces a report of a tournament given as PGN file
# It uses methods written in analysis.py

import analysis
import chess


def getPlayers(pgnPath: str) -> list:
    """
    This function gets the names of the players in a tournament.
    pgnPath: str
        The path to the PGN file of the tournament
    return -> list
        A list of the players' names
    """
    players = list()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            if (w := game.headers["White"]) not in players:
                players.append(w)
            if (b := game.headers["Black"]) not in players:
                players.append(b)
    print(players)
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
    This functions gets the scores for all players in a tournamet
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


if __name__ == '__main__':
    t = '../out/candidates2024-WDL+CP.pgn'
    players = getPlayers(t)
    # generateAccDistributionGraphs(t, players)
    print(getPlayerScores(t))
