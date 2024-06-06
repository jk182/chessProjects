# This file should contain different functions to analyse a chess game
# TODO: analysis with WDL+CP is very janky
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chess import engine, pgn, Board
import chess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import functions
from functions import configureEngine, sharpnessLC0
import logging
import evalDB


def analyseGames(pgnPath: str, outfile: str, sf: engine, lc0: engine, timeLimit: int, nodeLimit: int) -> None:
    """
    This function analyses a PGN and generates a new PGN with the analysis in the comments.
    It replaces the makeComments function
    pgnPath: str
        Path to the PGN file with the games to analyse
    outfile: str
        The path to the output PGN file
    sf: engine
        Configured Stockfish
    lc0: engine
        Configured LC0
    timeLimit: int
        Time limit for the Stockfish analysis
    nodeLimit: int
        Node limit for the LC0 analysis
    """
    gameNr = 1
    with open(pgnPath, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            print(f'Starting to analyse game {gameNr}')
            gameNr += 1

            board = game.board()

            newGame = chess.pgn.Game()
            newGame.headers = game.headers
            node = newGame

            for move in game.mainline_moves():
                print(move)
                node = node.add_variation(move)
                board.push(move)


                pos = board.fen()
                posDB = functions.modifyFEN(pos)
                if evalDB.contains(posDB):
                    evalDict = evalDB.getEval(posDB)
                    wdl = evalDict['wdl']
                    cp = evalDict['cp']
                    if evalDict['depth'] <= 0:
                        info = analysisCP(board, sf, timeLimit)
                        cp = info['score']
                        depth = info['depth']
                        evalDB.update(position=posDB, cp=cp, depth=depth)
                    if evalDict['nodes'] <= 0:
                        info = analysisWDL(board, lc0, nodeLimit)
                        wdl = list(chess.engine.PovWdl.white(info['wdl']))
                        print(wdl)
                        evalDB.update(position=posDB, nodes=nodeLimit, w=wdl[0], d=wdl[1], l=wdl[2])
                        print(f'WDL calculated: {wdl}')
                    print('Cache hit!')
                    print(wdl, cp)
                    node.comment = f'{str(wdl)};{cp}'
                else:
                    iSF = analysisCP(board, sf, timeLimit)
                    iLC0 = analysisWDL(board, lc0, nodeLimit)
                    if iSF and iLC0:
                        ana = formatInfo(iLC0, iSF)
                        print(ana)
                        node.comment = ana
                        cp = int(ana.split(';')[1])
                        wdl = [ int(w) for w in ana.split(';')[0].replace('[', '').replace(']', '').strip().split(',') ]
                        evalDB.insert(posDB, nodes=nodeLimit, cp=cp, w=wdl[0], d=wdl[1], l=wdl[2], depth=iSF['depth'])
            print(newGame, file=open(outfile, 'a+'), end='\n\n')



def makeComments(gamesFile: str, outfile: str, analysis, limit: int, engine: engine, cache: bool = False) -> list:
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
    engine: engine
        The engine to analyse. Note that it must fit with the analysis function (a bit inelegant)
    cache: bool
        If this is set to true, caching will be enabled, using evalDB
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
                if cache:
                    pos = board.fen()
                    posDB = functions.modifyFEN(pos)
                    if evalDB.contains(posDB):
                        # TODO: not general enough
                        evalDict = evalDB.getEval(posDB)
                        wdl = evalDict['wdl']
                        cp = evalDict['cp']
                        if evalDict['depth'] <= 0:
                            info = analysisCP(board, None, 4)
                            cp = info['score']
                        if evalDict['nodes'] <= 0:
                            wdl = analysisWDL(board, engine, limit)
                            wdlList = [int(x) for x in wdl[1:-1].split(',')]
                            print(wdlList)
                            evalDB.update(position=posDB, nodes=limit, w=wdlList[0], d=wdlList[1], l=wdlList[2])
                            print(f'WDL calculated: {wdl}')
                        print('Cache hit!')
                        print(wdl, cp)
                        node.comment = f'{str(wdl)};{cp}'
                    else:
                        infos = analysis(board, engine, limit)
                        if infos:
                            iLC0, iSF = infos
                            ana = formatInfo(iLC0, iSF)
                            print(ana)
                            node.comment = ana
                            cp = int(ana.split(';')[1])
                            wdl = [ int(w) for w in ana.split(';')[0].replace('[', '').replace(']', '').strip().split(',') ]
                            evalDB.insert(posDB, nodes=limit, cp=cp, w=wdl[0], d=wdl[1], l=wdl[2], depth=iSF['depth'])
                else:
                    node.comment = analysis(board, engine, limit)
            print(newGame, file=open(outfile, 'a+'), end='\n\n')
    # engine.quit()
    return []


def analysisWDL(position: Board, lc0: engine, limit: int, time: bool = False):
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
        return None
    
    if time:
        info = lc0.analyse(position, chess.engine.Limit(time=limit))
    else:
        info = lc0.analyse(position, chess.engine.Limit(nodes=limit))
    return info


def analysisCP(position: Board, sf: engine, timeLimit: int):
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
    # TODO: fix this somehow
    # sf = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    if position.is_game_over():
        return None

    info = sf.analyse(position, chess.engine.Limit(time=timeLimit))
    # sf.quit()
    return info


def analysisCPnWDL(position: Board, lc0: engine, nodes: int) -> tuple:
    """
    This function analyses a position both with LC0 and Stockfish. It returns the WDL and CP infos as tuple.
    """
    if position.is_game_over():
        return None

    # Defining Stockfish here is not ideal, but it's the easiest way right now
    sf = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    iLC0 = lc0.analyse(position, chess.engine.Limit(nodes=nodes))
    iSF = sf.analyse(position, chess.engine.Limit(time=4))
    sf.quit()
    return (iLC0, iSF)


def formatInfo(infoLC0 = None, infoSF = None) -> str:
    """
    This function takes the info from an engine analysis by LC0 or stockfish and returns the WDL/CP as string
    """
    evaluation = ""
    if infoLC0:
        wdl = []
        wdl_w = engine.PovWdl.white(infoLC0['wdl'])
        for w in wdl_w:
            wdl.append(w)
        evaluation = str(wdl)
    if infoSF:
        if infoLC0:
            evaluation += ';'
        cp = str(infoSF['score'].white())
        if '#' in cp:
            if '+' in cp:
                cp = 10000
            else:
                cp = -10000
        evaluation += str(cp)
    return evaluation


def sharpnessChangePerPlayer(pgnPath: str, startSharp: float = 0.468) -> dict:
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
                    if ';' in node.comment:
                        c = node.comment.split(';')[0]
                    else:
                        c = node.comment
                    wdl = [ int(w) for w in c.replace('[', '').replace(']', '').strip().split(',') ]
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

            plt.show()


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


def getCPLDistributionPlayer(pgnPath: str, player: str) -> dict:
    """
    This method calculated the CPL for a player on each moves.
    pgnPath: str
        The path to the PGN file
    player: str
        The name of the player
    return -> dict
        A dictionary with the CPL as keys and the number of moves with this CPL as values
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
    return cpl


def plotCPLDistributionPlayer(pgnPath: str, player: str):
    """
    This method plots a centipawn distribution from the comments of a PGN file for a specific player.
    It plots all games in the file in one graph
    pgnPath: str
        The path to the PGN file
    player: str
        The name of the player
    """
    cpl = getCPLDistributionPlayer(pgnPath, player)

    fig, ax = plt.subplots()
    # ax.set_yscale("log")
    xy = [ (k,v) for k,v in cpl.items() if k > 0]
    ax.bar([x[0] for x in xy], [y[1] for y in xy], width=1, color='darkgrey')
    plt.xlim(0, 305)
    plt.savefig('../out/CPL2.png', dpi=500)
    plt.show()


def getAccuracyDistributionPlayer(pgnPath: str, player: str) -> dict:
    """
    This method calculated the accuracy for a player on each moves.
    pgnPath: str
        The path to the PGN file
    player: str
        The name of the player
    return -> dict
        A dictionary with the accuracy as keys and the number of moves with this accuracy as values
    """
    with open(pgnPath, 'r') as pgn:
        accDis = dict()
        while (game := chess.pgn.read_game(pgn)):
            if player == game.headers["White"]:
                white = True
            elif player == game.headers["Black"]:
                white = False
            else:
                continue
            node = game
            lastWp = None

            while not node.is_end():
                node = node.variations[0]
                if node.comment != 'None' and node.comment:
                    if '#' in node.comment:
                        break

                    if ';' in node.comment:
                        # int(float()) because '28.0' cannot be converted to an int
                        cp = int(float(node.comment.split(';')[-1]))
                    else:
                        cp = int(node.comment)
                    wp = functions.winP(cp)
                    if lastWp is not None:
                        if not node.turn() and white:
                            acc = min(100, functions.accuracy(lastWp, wp))
                            acc = int(acc)
                            if acc in accDis.keys():
                                accDis[acc] += 1
                            else:
                                accDis[acc] = 1
                        elif node.turn() and not white:
                            acc = min(100, functions.accuracy(wp, lastWp))
                            acc = int(acc)
                            if acc in accDis.keys():
                                accDis[acc] += 1
                            else:
                                accDis[acc] = 1
                    lastWp = wp
    return accDis


def plotAccuracyDistributionPlayer(pgnPath: str, player: str, outFile: str = None):
    """
    This method plots an accuracy distribution from the comments of a PGN file for a specific player.
    It plots all games in the file in one graph
    pgnPath: str
        The path to the PGN file
    player: str
        The name of the player
    outFile: str
        Filename of the plot if it should be saved instead of shown
    """
    accDis = getAccuracyDistributionPlayer(pgnPath, player)
    p = player.split(',')[0]

    fig, ax = plt.subplots()
    ax.set_yscale("log")

    xy = [ (k,v) for k,v in accDis.items() if k <= 100]
    nMoves = sum(accDis.values())
    ax.bar([x[0] for x in xy], [y[1]/nMoves for y in xy], width=1, color='#689bf2', edgecolor='black', linewidth=0.5)

    plt.xlim(0, 100)
    ax.invert_xaxis()
    ax.set_xlabel('Move Accuracy')
    ax.set_ylabel('Relative number of moves')
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.15, right=0.95)
    plt.title(f'Accuracy per move: {p}')
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
    ax.yaxis.get_major_formatter().set_scientific(False)

    if outFile:
        plt.savefig(outFile, dpi=500)
    else:
        plt.show()


def plotSharpChange(sharpChange: dict, player: str = '', short: dict = None, filename: str = None):
    """
    This function takes a dictionary with the sharpness change per move and plots the average as a bar chart.
    A player name can be specified if one is only interested in the sharpness for this player.
    sharpChange: dict
        The sharpness change
    player: str
        The name of the player one is interested in
    short: dict
        This a dictionary with a short form of players' names
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved
    """
    x = list()
    y = list()
    for p,sharp in sharpChange.items():
        if player in p:
            # one sharp change was infinite, so I exclude them (TODO: investigate this)
            finSharp = [ s for s in sharp if not np.isinf(s) ]
            pl = p.split(',')[0]
            pl = p
            if short:
                if pl in short.keys():
                    pl = short[pl]
            x.append(pl)
            y.append(sum(finSharp)/len(finSharp))

    fig, ax = plt.subplots()
    plt.xticks(rotation=90)
    ax.set_facecolor('#e6f7f2')
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.15, right=0.95)
    plt.xlim(-0.5, len(x)-0.5)
    ax.bar(x,y, edgecolor='black', linewidth=0.5, color='#fa5a5a', width=0.7)
    ax.set_ylabel('Average sharpness change per move')
    # ax.legend(['Avg. sharp change per move'])
    plt.title('Average sharpness change per move')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
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
    sf = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    """
    info = leela.analyse(Board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'), chess.engine.Limit(nodes=5000))
    wdl = []
    wdl_w = engine.PovWdl.white(info['wdl'])
    for w in wdl_w:
        wdl.append(w)
    startSharp = sharpnessLC0(wdl)
    """
    candidates = '../resources/wijkMasters2024.pgn'
    outCan = '../out/wijk2024.pgn'
    # makeComments(candidates, outCan, analysisCPnWDL, 5000, leela, True)

    """
    tournaments = ['arjun_biel.pgn', 'carlsen_open.pgn']
    for t in tournaments:
        print(t)
        makeComments(f'../resources/{t}', f'../out/{t[:-4]}-5000-30.pgn', analysisCPnWDL, 5000, leela, True)
    """

    # analyseGames('../resources/sharjah.pgn', '../out/sharjah-out.pgn', sf, leela, 4, 5000)
    analyseGames('../resources/womenCandidates2024.pgn', '../out/womenCandidates2024-out.pgn', sf, leela, 4, 5000)
    analyseGames('../resources/norwayChessOpen2024.pgn', '../out/norwayChessOpen2024-out.pgn', sf, leela, 4, 5000)
    analyseGames('../resources/norwayChessWomen2024.pgn', '../out/norwayChessWomen2024-out.pgn', sf, leela, 4, 5000)
    analyseGames('../resources/grandSwiss2023.pgn', '../out/grandSwiss2023-out.pgn', sf, leela, 4, 5000)
    sf.quit()
    leela.quit()
    """
    playerSharp = sharpnessChangePerPlayer(candidates, startSharp)
    for k,v in playerSharp.items():
        print(k, sum(v)/len(v))
    """
    # stockfish = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    dub = '../resources/dubov.pgn'
    of = '../out/dubov-wdl.pgn'
    # makeComments('../resources/carlsen2019-2.pgn', '../out/carlsen2019-5000.pgn', analysisWDL, 5000, leela)
    # for k,v in sharpnessChangePerPlayer('../out/tal-botvinnik-1960-5000.pgn', 0.468).items():
    #     print(k, sum(v)/len(v))
    carlsen = ['../out/carlsen2014-5000.pgn', '../out/carlsen2019-5000.pgn']
    """
    for c in carlsen:
        for k,v in sharpnessChangePerPlayer(c, 0.468).items():
            if 'Carlsen' in k:
                nv = [val for val in v if not np.isinf(val)]
                print(k, sum(nv)/len(nv))
    """
    # plotSharpChange(sharpnessChangePerPlayer(candidates))
    pgn = '../resources/naka-nepo.pgn'
    outf = '../out/naka-nepo-30000.pgn'
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
    # plotAccuracyDistributionPlayer('../out/myGames-sf.pgn', 'Kern, Julian')
    # plotAccuracyDistribution('../out/Vidit-Caruana-sf.pgn')
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
    logging.basicConfig(level=logging.WARNING)
    pgn = '../resources/jkGames50.pgn'
    fen = 'rnbqkb1r/pp2pppp/3p1n2/2p5/4P3/2P2N2/PP1PBPPP/RNBQK2R b KQkq - 2 4'
    maiaFolder = '/Users/julian/chess/maiaNets'
    # print(maiaMoves([fen], maiaFolder))
    """
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
