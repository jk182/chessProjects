# This file should contain different functions to analyse a chess game

from chess import engine, pgn, Board
import chess
import numpy as np
import matplotlib.pyplot as plt
from functions import configureEngine, sharpnessLC0
import logging


def makeComments(gamesFile: str, outfile: str, analysis, limit: int, engine: engine) -> list:
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
                node.comment = analysis(board, engine, limit)
            print(newGame, file=open(outfile, 'a+'), end='\n\n')
    engine.quit()
    return []


def analysisWDL(position: Board, lc0: engine, limit: int, time: bool = False) -> str:
    """
    This function analyses a given chess position with LC0 to get the WDL from whtie's perspective.
    position:Board
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


def analysisCP(position: Board, sf: engine, timeLimit: int) -> str:
    """
    This function analyses a given position with Stockfish and returns the centipawn score.
    position: Board:
        The position to analyse
    sf:engine
        Stockfish as a configured chess engine
    timeLimit:int
        The time in seconds spent on the position
    return -> str
        The centipawn score
    """
    if position.is_game_over():
        return ""

    info = sf.analyse(position, chess.engine.Limit(time=timeLimit))
    return str(info['score'].white())


def sharpnessChangePerPlayer(pgnPath: str, startSharp: float = 0.47) -> dict:
    """
    This function takes the path to a PGN file with analysed WDL values and returns the sharpness change per player.
    pgnPath: str
        The path to the analysed WDL file
    startSharp: float
        The sharpness of the starting position
    return -> dict
        A dictionary with the player names as keys and their sharpness changes as values
    """
    sharpPlayer = dict()
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            node = game
            white = game.headers["White"]
            black = game.headers["Black"]
            # Sharpness of the starting position
            lastSharp = startSharp

            while not node.is_end():
                node = node.variations[0]
                # None should only happen if there is a forced mate
                if node.comment != 'None' and node.comment:
                    wdl = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                    sharp = sharpnessLC0(wdl)
                    diff = sharp-lastSharp
                    lastSharp = sharp
                    if not node.turn():
                        if white in sharpPlayer.keys():
                            sharpPlayer[white].append(diff)
                        else:
                            sharpPlayer[white] = [diff]
                    elif node.turn():
                        if black in sharpPlayer.keys():
                            sharpPlayer[black].append(diff)
                        else:
                            sharpPlayer[black] = [diff]
    return sharpPlayer



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
    mis = 150
    lastWDL = None
    positions = list()
    sf = configureEngine('stockfish', {'Threads': '9', 'Hash': '8192'})
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            node = game
            while not node.is_end():
                if node.comment:
                    lastWDL = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                else:
                    node = node.variations[0]
                    continue
                board = node.board()
                pos = board.fen()
                node = node.variations[0]
                if node.comment:
                    currWDL = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                    if node.turn() == chess.WHITE:
                        diff = currWDL[0]+currWDL[1]*0.5-(lastWDL[0]+lastWDL[1]*0.5)
                    else:
                        diff = currWDL[2]+currWDL[1]*0.5-(lastWDL[2]+lastWDL[1]*0.5)
                    if diff > mis:
                        bestMove = sf.analyse(board, chess.engine.Limit(depth=20))['pv'][0]
                        positions.append((board.san(node.move), pos, board.san(bestMove)))
    sf.quit()
    return positions


def plotWDL(pgnPath: str):
    """
    This method plots the WDL from the comments of a PGN file
    pgnPath: str
        The path to a PGN file where the comments are the WDLs
    """
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            node = game
            white = game.headers["White"]
            black = game.headers["Black"]
            event = game.headers["Event"]
            w = []
            d = []
            l = []

            while not node.is_end():
                node = node.variations[0]
                # None should only happen if there is a forced mate
                if node.comment != 'None' and node.comment:
                    wdl = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
                    w.append(wdl[0]/1000)
                    d.append(wdl[1]/1000)
                    l.append(wdl[2]/1000)
            y = np.vstack([w, d, l])
            
            fig, ax = plt.subplots()
            plt.ylim(0,1)
            plt.xlim(0,len(w)-1)
            ax.stackplot(range(len(w)), y, colors=["#FDFDFD", "#989898", "#020202"])
            plt.savefig(f'../out/WDLplots/{white}-{black},{event}.png')

            # plt.show()


def plotCPLDistribution(pgnPath: str):
    """
    This method plots a centipawn distribution from the comments of a PGN file
    pgnPath: str
        The path to the PGN file
    """
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            node = game
            wCPL = dict()
            bCPL = dict()
            lastCP = None

            while not node.is_end():
                node = node.variations[0]
                if node.comment != 'None' and node.comment:
                    if '#' in node.comment:
                        break
                    cp = int(node.comment)
                    if lastCP is not None:
                        if not node.turn():
                            cpl = max(0, lastCP-cp)
                            if cpl in wCPL.keys():
                                wCPL[cpl] += 1
                            else:
                                wCPL[cpl] = 1
                        else:
                            cpl = max(0, cp-lastCP)
                            if cpl in bCPL.keys():
                                bCPL[cpl] += 1
                            else:
                                bCPL[cpl] = 1
                        # print(node.turn(), node.move, node.comment, lastCP, cp)
                    lastCP = cp

            fig, ax = plt.subplots()
            ax.set_facecolor("grey")
            ax.bar(wCPL.keys(), wCPL.values(), color="white", width=1)
            ax.bar(bCPL.keys(), bCPL.values(), color="black", width=1)
            plt.xlim(-1, 350)
            plt.savefig('../out/CPL1.png', dpi=500)
            plt.show()


def plotCPLDistributionPlayer(pgnPath: str, player: str):
    """
    This method plots a centipawn distribution from the comments of a PGN file for a specific player.
    It plots all games in the file in one graph
    pgnPath: str
        The path to the PGN file
    player: str
        The name of the player
    """
    with open(pgnPath, 'r') as pgn:
        cpl = dict()
        while (game := chess.pgn.read_game(pgn)):
            if player == game.headers["White"]:
                white = True
            elif player == game.headers["Black"]:
                white = False
            else:
                continue
            node = game
            lastCP = None

            while not node.is_end():
                node = node.variations[0]
                if node.comment != 'None' and node.comment:
                    if '#' in node.comment:
                        break
                    cp = int(node.comment)
                    if lastCP is not None:
                        if not node.turn() and white:
                            curCPL = max(-10, lastCP-cp)
                            curCPL = min(curCPL, 300)
                            if curCPL in cpl.keys():
                                cpl[curCPL] += 1
                            else:
                                cpl[curCPL] = 1
                        elif node.turn() and not white:
                            curCPL = max(-10, cp-lastCP)
                            curCPL = min(curCPL, 300)
                            if curCPL in cpl.keys():
                                cpl[curCPL] += 1
                            else:
                                cpl[curCPL] = 1
                    lastCP = cp

    fig, ax = plt.subplots()
    # ax.set_yscale("log")
    xy = [ (k,v) for k,v in cpl.items() if k > 0]
    ax.bar([x[0] for x in xy], [y[1] for y in xy], width=1, color='darkgrey')
    plt.xlim(0, 305)
    plt.savefig('../out/CPL2.png', dpi=500)
    plt.show()



def maiaMoves(positions: list, maiaFolder: str) -> dict:
    """
    This function analyses a given position with various Maia models and returns the best move as a string
    positions: list
        The positions as a list of FEN strings
    maiaFolder: str
        The folder containing the Maia models, which should be named 'maia-{rating}.pb'
    return: dict
        The the positions and moves from the various models in a dictionary
    """
    ret = dict()
    for pos in positions:
        ret[pos] = list()

    for i in range(1, 10):
        # starting the engine new each loop seems wasteful but it gets rid of a caching problem
        # maia = configureEngine('/home/julian/lc0/build/release/lc0', {'UCI_ShowWDL': 'true'})
        maia = configureEngine('/opt/homebrew/Cellar/lc0/0.30.0/bin/lc0', {'UCI_ShowWDL': 'true'})
        w = f'{maiaFolder}/maia-1{i}00.pb.gz'
        maia.configure({'WeightsFile': w})
        moves = list()
        for pos in positions:
            board = Board(pos)
            info = maia.analyse(board, chess.engine.Limit(nodes=1))
            print(info)
            ret[pos].append(board.san(info['pv'][0]))
        maia.quit()
    return ret


if __name__ == '__main__':
    op = {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'}
    leela = configureEngine('lc0', op)
    info = leela.analyse(Board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'), chess.engine.Limit(nodes=5000))
    wdl = []
    wdl_w = engine.PovWdl.white(info['wdl'])
    for w in wdl_w:
        wdl.append(w)
    startSharp = sharpnessLC0(wdl)
    candidates = '../../projects/chess/candidates_5000n.pgn'
    """
    playerSharp = sharpnessChangePerPlayer(candidates, startSharp)
    for k,v in playerSharp.items():
        print(k, sum(v)/len(v))
    """
    # stockfish = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    dub = '../resources/dubov.pgn'
    of = '../out/dubov-wdl.pgn'
    makeComments('../resources/carlsen2019-2.pgn', '../out/carlsen2019-5000.pgn', analysisWDL, 5000, leela)
    for k,v in sharpnessChangePerPlayer('../out/tal-botvinnik-1960-5000.pgn', 0.468).items():
        print(k, sum(v)/len(v))
    pgn = '../resources/Firouzja-Gukesh.pgn'
    outf = '../out/Firouzja-Gukesh-30000.pgn'
    # makeComments(pgn, outf, analysisWDL, 30000, leela)
    # plotWDL(outf)
    pgns = ['../resources/Tal-Koblents-1957.pgn',
            '../resources/Ding-Nepo-G12.pgn',
            '../resources/Ponomariov-Carlsen-2010.pgn',
            '../resources/Vidit-Carlsen-2023.pgn']
    praggNepo = '../resources/Pragg-Nepo.pgn'
    adventOpen = '../resources/Advent-Open.pgn'
    myGames = '../resources/Austria-Open.pgn'
    # makeComments(myGames, '../out/myGames-sf.pgn',  analysisCP, 4, stockfish)
    # makeComments('../resources/Vidit-Caruana.pgn', '../out/Vidit-Caruana-sf.pgn', analysisCP, 4, stockfish)
    # plotCPLDistribution('../out/Firouzja-Gukesh-sf.pgn')
    # plotCPLDistributionPlayer('../out/myGames-sf.pgn', 'Kern, Julian')
    # plotCPLDistribution('../out/Vidit-Caruana-sf.pgn')
    # pgns = ['../resources/Ponomariov-Carlsen-2010.pgn']
    # Testing for WDL graphs post
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
    # Testing for Maia mistake analysis
    """
    logging.basicConfig(level=logging.WARNING)
    pgn = '../resources/jkGames50.pgn'
    fen = '8/8/6p1/2pK3p/1k5P/1P4P1/8/8 w - - 0 44'
    maiaFolder = '/Users/julian/chess/maiaNets'
    # print(maiaMoves(fen, maiaFolder))
    # print(findMistakes('../out/Ponomariov-Carlsen-2010-15000.pgn'))
    # makeComments(pgn, '../out/jkGames50-10000.pgn', analysisWDL, 10000, op)
    # mistakes = findMistakes('../out/jkGames50-10000.pgn')
    # print(mistakes)
    mistakePositions = [ m[1] for m in mistakes ]
    maiaM = maiaMoves(mistakePositions, maiaFolder)
    for m in mistakes:
        print(f'Position: {m[1]}')
        print(f'Game move: {m[0]}')
        print(f'Best move: {m[2]}')
        print(maiaM[m[1]])
    """
