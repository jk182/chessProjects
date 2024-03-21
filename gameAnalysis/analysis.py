# This file should contain different functions to analyse a chess game

from chess import engine, pgn, Board
import chess
import numpy as np
import matplotlib.pyplot as plt
from functions import configureEngine


def makeComments(gamesFile: str, outfile: str, analysis, nodes: int, options: dict) -> list:
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
    
    leela = configureEngine('/home/julian/lc0/build/release/lc0', options)

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
                print(move)
                # Checks if we have the starting position and need to make a new node
                if board == game.board():
                    node = newGame.add_variation(move)
                else:
                    node = node.add_variation(move)

                board.push(move)
                # Adds a comment after every move with the wdl
                node.comment = analysis(board, leela, nodes)
            print(newGame, file=open(outfile, 'a+'), end='\n\n')
    leela.quit()
    return []


def analysisWDL(position: Board, lc0: engine, limit: int, time: bool = False) -> str:
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
        info = lc0.analyse(position, chess.engine.Limit(time=limit))
    else:
        info = lc0.analyse(position, chess.engine.Limit(nodes=limit))

    wdl = []
    wdl_w = engine.PovWdl.white(info['wdl'])
    for w in wdl_w:
        wdl.append(w)
    return str(wdl)


def plotWDL(pgnPath: str):
    """
    This method plots the WDL from the comments of a PGN file
    pgnPath: str
        The path to a PGN file where the comments are the WDLs
    """
    with open(pgnPath, 'r') as pgn:
        gameNr = 1
        while (game := chess.pgn.read_game(pgn)):
            print(gameNr)
            gameNr += 1
            node = game
            w = []
            d = []
            l = []

            while not node.is_end():
                node = node.variations[0]
                # None should only happen if there is a forced mate
                if node.comment != 'None':
                    wdl = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                    w.append(wdl[0])
                    d.append(wdl[1])
                    l.append(wdl[2])
            y = np.vstack([w, d, l])
            
            fig, ax = plt.subplots()
            plt.ylim(0,1000)
            plt.xlim(0,len(w)-1)
            ax.stackplot(range(len(w)), y)
            plt.savefig(f'../out/WDLplots/{pgnPath.split("/")[-1][:-4]}.png')

            # plt.show()



if __name__ == '__main__':
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'}
    pgns = ['../resources/Tal-Koblents-1957.pgn',
            '../resources/Ding-Nepo-G12.pgn',
            '../resources/AZ-SF-Qh1.pgn',
            '../resources/AZ-SF-Matrix.pgn']
    pgns = ['../resources/Anand-Carlsen-2013-G4.pgn']
    nodes = [1, 10, 100, 1000, 10000]
    for pgn in pgns:
        print(f'Analysing {pgn}')
        for n in nodes:
            name = pgn.split('/')[-1]
            outf = f'../out/{name[:-4]}-N{n}.pgn'
            makeComments(pgn, outf, analysisWDL, n, op)
            plotWDL(outf)
    """
    pgn = '../resources/Ponomariov-Carlsen-2010.pgn'
    outf = '../out/Ponomariov-Carlsen-2010-15000.pgn'
    makeComments(pgn, outf, analysisWDL, nodes, op)
    outf2 = '../out/Ponomariov-Carlsen-2010-15000-2800.pgn'
    """
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLDrawRateReference': '0.58', 'WDLCalibrationElo': '2800', 'ContemptMode':'black_side_analysis', 'WDLEvalObjectivity': '0.0', 'ScoreType':'WDL_mu'}
    for pgn in pgns:
        name = pgn.split('/')[-1]
        outf = f'../out/{name[:-4]}-N10000-2800.pgn'
        makeComments(pgn, outf, analysisWDL, 10000, op)
        plotWDL(outf)
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLDrawRateReference': '0.58', 'WDLCalibrationElo': '2800', 'Contempt': '100', 'ContemptMode':'black_side_analysis', 'WDLEvalObjectivity': '0.0', 'ScoreType':'WDL_mu'}

    for pgn in pgns:
        name = pgn.split('/')[-1]
        outf = f'../out/{name[:-4]}-N10000-2800-150.pgn'
        makeComments(pgn, outf, analysisWDL, 10000, op)
        plotWDL(outf)
    """
    plotWDL(outf)
    plotWDL(outf2)
    plotWDL(outf3)
    """
