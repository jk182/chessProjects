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
        while game := chess.pgn.read_game():
            if w := game.headers["White"] not in players:
                players.append(w)
            if b := game.headers["Black"] not in players:
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
    
