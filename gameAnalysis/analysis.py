# This file should contain different functions to analyse a chess game

from chess import engine, pgn
import chess
import numpy as np
import matplotlib.pyplot as plt
from chessProjects.sharpnessXaccuracy.functions import configureEngine


def makeComments(gamesFile: str, outfile: str, analysis) -> list:
    """
    This function plays thorugh the games in a file and makes comments to them.
    The specific comments depend on the analysis method chosen
    gamesFile: str
        The name of a PGN file containing the games to analyse
    outfile: str
        The path of the output PGN file with the WDL comments
    analysis
        This is a function which analyses to positions. I kept it separate sicne 
        it's easier to change the type of analysis (WDL, centipawns, ...)
    return -> list
        A list of lists for each game, containing the WDL and score after every move
    """
    
    leela = configureEngine('/home/julian/lc0/build/release/lc0', {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'})

    gameNR = 1
    with open(gamesFile, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            print(f'Starting with game {gameNR}...')
            gameNR += 1

            board = game.board()
            
            # I found no way to add comments to an existing PGN, so I create a new PGN with the comments
            newGame = chess.pgn.Game()
            newGame.headers = game.headers

            for move in game.mainline_moves():
                # Checks if we have the starting position and need to make a new node
                if board == game.board():
                    node = newGame.add_variation(move)
                else:
                    node = node.add_variation(move)

                board.push(move)
                # Adds a comment after every move with the wdl
                node.comment = analysis(board, leela, 10000)
            print(newGame, file=open(outfile, 'a+'), end='\n\n')

    return []


def analysisWDL(position: board, lc0: engine, limit: int, time: bool = False) -> str:
    """
    This function analyses a given chess position with LC0 to get the WDL from whtie's perspective.
    position:baord
        The position to analyse
    lc0:engine
        LC0 already as a chess engine
    limit:int
        The limit for the analysis, default is nodes, but time can also be selected
    time:bool = False
        If this is true, the limit will be for the time in seconds
    return -> str
        The formated WDL
    """
    # The analyse() method gives an error if the game is over (i.e. checkmate, stalemate or insuffucient material)
    if position.is_game_over():
        return ""
    
    if time:
        info = lc0.analyse(board, chess.engine.Limit(time=limit))
    else:
        info = lc0.analyse(board, chess.engine.Limit(node=limit))

    wdl = []
    wdl_w = engine.PovWdl.white(info['wdl'])
    for w in wdl_w:
        wdl.append(w)
    return str(wdl)
