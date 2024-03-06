from chess import engine, pgn
import chess
import matplotlib.pyplot as plt
import functions
import numpy as np


def annotate(gamesFile: str, outfile: str, lc0: engine, sf: engine, nodes: int) -> list:
    """
    This function plays thorugh the games in a file, analyses them and returns a
    list of the evaluations and WDL after every move
    gamesFile: str
        The name of a PGN file containing the games to analyse
    outfile: str
        The path of the output PGN file with the WDL comments
    lc0: engine
        LC0 as an engine
    sf: engine
        Stockfish
    nodes: int
        The number of nodes searched for every move
    return -> list
        A list of lists for each game, containing the WDL and score after every move
    """

    depth = 18
    s = ''
    gameNR = 1
    with open(gamesFile, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            print(f'Starting with game {gameNR}...')
            gameNR += 1

            if s:
                s += '\n'

            board = game.board()

            # I found no way to add comments to an existing PGN, so I create a new PGN with the comments
            newGame = chess.pgn.Game()
            newGame.headers = game.headers

            for move in game.mainline_moves():
                # print(move)
                # Checks if we have the starting position and need to make a new node
                if board == game.board():
                    node = newGame.add_variation(move)
                else:
                    node = node.add_variation(move)

                board.push(move)
                # The analyse() method gives an error if the game is over (i.e. checkmate, stalemate or insuffucient material)
                if not board.is_game_over():
                    c = not board.turn
                    cp = sf.analyse(board, chess.engine.Limit(depth=depth))["score"].pov(c).score()
                    info = lc0.analyse(board, chess.engine.Limit(nodes=nodes))
                    # score = str(info['score'].white())  # The accuracy metric only needs the win percentage
                    wdl = functions.formatWDL(info['wdl'])
                    s += str(wdl)

                # Adds a comment after every move with the wdl
                node.comment = f'{str(wdl)};{cp}'
            print(newGame, file=open(outfile, 'a+'), end='\n\n')

    # print(s, file=open(outfile, 'w'))


def readComments(pgnfile: str) -> list:
    """
    This function takes a PGN files and reads the WDL comments and converts them to an accuracy-sharpness-list
    pgnfile: str
        The path of the PGN file
    return -> list
        The accuracy-sharpness-list created from the WDL comments of the PGN file
    """

    out = list()
    with open(pgnfile, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            cp = -29
            wdl = [210, 620, 170]
            whiteMove = True
            node = game
            game = list()

            while not node.is_end():
                node = node.variations[0]
                # None should only happen if there is a forced mate
                if node.comment.split(';')[1] != 'None':
                    # sharpness = sharpnessOG(wdl)
                    sharpness = functions.sharpnessLC0(wdl)
                    winP = functions.winP(cp*(-1))

                    wdll = node.comment.split(';')[0]
                    wdl = [ int(w) for w in wdll.replace('[', '').replace(']', '').strip().split(',') ]
                    cp = int(node.comment.split(';')[1])

                    newWinP = functions.winP(cp)
                    acc = functions.accuracy(winP, newWinP)

                    game.append((acc, sharpness))
                whiteMove = not whiteMove
            out.append(game)

    return out


def accuracySharpnessCorr(accSharp: list, plys: int = 0):
    """
    This function plots the accuracy and sharpness on a graph
    accSharp: list
        The list containing accuracy and sharpness for the moves in the format of analyseFile
    plys: int
        The number of plys which will be ignored at the beginning of each game (opening theory)
    """
    # Testing on the candidates_5000n.pgn gave the highest correlation (-0.16) for plys=30
    acc = list()
    sharp = list()

    for game in accSharp:
        for i, g in enumerate(game):
            if i >= plys:
                acc.append(g[0])
                sharp.append(g[1])
    
    print(np.corrcoef(sharp, acc))
    plt.scatter(sharp, acc, c='grey', alpha=0.3, s=3)
    plt.show()


def accuracyPerSharpness(accSharp: list, maxSharpness: float, intervalls: int, plys: int = 0):
    """
    This function calculates and plots the accuracy in different sharpness ranges
    accSharp: list
        The list containing accuracy and sharpness for the moves in the format of analyseFile
    maxSharpness: float
        The maximum sharpness, all positions with a higher sharpness are placed in the last intervall
    intervalls: int
        The number of intervalls in which the sharpness should be devided
    plys: int
        The number of plys which will be ignored at the start (opening theory)
    """
    acc = list()
    sharp = list()

    for game in accSharp:
        for i, g in enumerate(game):
            if i >= plys:
                acc.append(g[0])
                sharp.append(g[1])
    
    accPerS = list()
    for i in range(intervalls + 1):
        accPerS.append(list())
    for i, s in enumerate(sharp):
        if s >= maxSharpness:
            accPerS[intervalls].append(acc[i])
        else:
            accPerS[int((s * intervalls)/maxSharpness)].append(acc[i])
    
    averages = [ sum(a)/len(a) for a in accPerS ]
    print(averages)
    x = [ i * maxSharpness / intervalls for i in range(len(averages)) ]
    plt.plot(x, averages)
    plt.show()


if __name__ == '__main__':
    # leela = functions.configureEngine('/home/julian/lc0/build/release/lc0', {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'})
    # stockfish = functions.configureEngine('stockfish', {'Threads': '9', 'Hash': '8192'})
    # annotate('../resources/candidates_5000n.pgn', '../resources/candidates_out.pgn', leela, stockfish, 5000)
    # leela.quit()
    # stockfish.quit()
    sharpAcc = readComments('../resources/candidates_out.pgn')
    # print(accuracySharpnessCorr(sharpAcc, 10))
    accuracyPerSharpness(sharpAcc, 4, 16, 20)
