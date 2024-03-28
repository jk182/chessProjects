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


def findMistakes(pgnPath: str) -> list:
    """
    This function takes a PGN with WDL evaluations and finds the mistakes in the game
    pgnPath: str
        The path to the PGN file
    return: list
        A list with the positions where mistakes occured
    """
    # The number by which the win percentage has to decrease for the move to count as a mistake
    # Note that the WDL adds up to 1000, so 100 is equivalent to 10%
    mis = 100
    lastWDL = None
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            node = game
            while not node.is_end():
                if node.comment:
                    lastWDL = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                else:
                    node = node.variations[0]
                    continue
                node = node.variations[0]
                if node.comment:
                    currWDL = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                    if node.turn() == chess.WHITE:
                        diff = currWDL[0]+currWDL[1]*0.5-(lastWDL[0]+lastWDL[1]*0.5)
                    else:
                        diff = currWDL[2]+currWDL[1]*0.5-(lastWDL[2]+lastWDL[1]*0.5)
                    if diff > mis:
                        # Note that the colours are inverted since we are looking at the game after the mistake
                        print(node.turn())
                        print(diff)


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
                    w.append(wdl[0]/1000)
                    d.append(wdl[1]/1000)
                    l.append(wdl[2]/1000)
            y = np.vstack([w, d, l])
            
            fig, ax = plt.subplots()
            plt.ylim(0,1)
            plt.xlim(0,len(w)-1)
            ax.stackplot(range(len(w)), y)
            plt.savefig(f'../out/WDLplots/{pgnPath.split("/")[-1][:-4]}.png')

            # plt.show()


def maiaMoves(pos: str, maiaFolder: str) -> list:
    """
    This function analyses a given position with various Maia models and returns the best move as a string
    pos: str
        The position as a FEN string
    maiaFolder: str
        The folder containing the Maia models, which should be named 'maia-{rating}.pb'
    return: list
        The moves from the various models in a list
    """
    board = Board(pos)
    moves = list()
    for i in range(1, 10):
        # starting the engine new each loop seems wasteful but it gets rid of a caching problem
        maia = configureEngine('/home/julian/lc0/build/release/lc0', {'UCI_ShowWDL': 'true'})
        w = f'{maiaFolder}/maia-1{i}00.pb'
        maia.configure({'WeightsFile': w})
        info = maia.analyse(board, chess.engine.Limit(nodes=1))
        print(info)
        moves.append(board.san(info['pv'][0]))
        maia.quit()
    return moves


if __name__ == '__main__':
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'}
    pgns = ['../resources/Tal-Koblents-1957.pgn',
            '../resources/Ding-Nepo-G12.pgn',
            '../resources/Ponomariov-Carlsen-2010.pgn',
            '../resources/Vidit-Carlsen-2023.pgn']
    # pgns = ['../resources/Ponomariov-Carlsen-2010.pgn']
    """
    nodes = [1, 10, 100, 1000, 10000]
    for pgn in pgns:
        print(f'Analysing {pgn}')
        for n in nodes:
            name = pgn.split('/')[-1]
            outf = f'../out/{name[:-4]}-N{n}.pgn'
            # makeComments(pgn, outf, analysisWDL, n, op)
            plotWDL(outf)
    pgn = '../resources/Ponomariov-Carlsen-2010.pgn'
    outf = '../out/Ponomariov-Carlsen-2010-15000.pgn'
    makeComments(pgn, outf, analysisWDL, nodes, op)
    outf2 = '../out/Ponomariov-Carlsen-2010-15000-2800.pgn'
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLDrawRateReference': '0.58', 'WDLCalibrationElo': '2800', 'ContemptMode':'black_side_analysis', 'WDLEvalObjectivity': '0.0', 'ScoreType':'WDL_mu'}
    for pgn in pgns:
        name = pgn.split('/')[-1]
        outf = f'../out/{name[:-4]}-N10000-2800.pgn'
        # makeComments(pgn, outf, analysisWDL, 10000, op)
        plotWDL(outf)
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLDrawRateReference': '0.58', 'WDLCalibrationElo': '2800', 'Contempt': '100', 'ContemptMode':'black_side_analysis', 'WDLEvalObjectivity': '0.0', 'ScoreType':'WDL_mu'}

    for pgn in pgns:
        name = pgn.split('/')[-1]
        outf = f'../out/{name[:-4]}-N10000-2800-150.pgn'
        # makeComments(pgn, outf, analysisWDL, 10000, op)
        plotWDL(outf)
    plotWDL(outf)
    plotWDL(outf2)
    plotWDL(outf3)
    """
    fen = '8/8/6p1/2pK3p/1k5P/1P4P1/8/8 w - - 0 44'
    maiaFolder = '/home/julian/chess/maiaNets'
    # print(maiaMoves(fen, maiaFolder))
    print(findMistakes('../out/Ponomariov-Carlsen-2010-15000.pgn'))
