# This file should contain different functions to analyse a chess game

from chess import engine, pgn, Board
import chess
import numpy as np
import matplotlib.pyplot as plt
from functions import configureEngine
import logging


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
    pgns = ['../resources/Tal-Koblents-1957.pgn',
            '../resources/Ding-Nepo-G12.pgn',
            '../resources/Ponomariov-Carlsen-2010.pgn',
            '../resources/Vidit-Carlsen-2023.pgn']
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
    fen = '8/8/6p1/2pK3p/1k5P/1P4P1/8/8 w - - 0 44'
    maiaFolder = '/Users/julian/chess/maiaNets'
    # print(maiaMoves(fen, maiaFolder))
    # print(findMistakes('../out/Ponomariov-Carlsen-2010-15000.pgn'))
    # makeComments(pgn, '../out/jkGames50-10000.pgn', analysisWDL, 10000, op)
    # mistakes = findMistakes('../out/jkGames50-10000.pgn')
    mistakes = [('Nf3', 'r1bqk2r/p2pppbp/2p2np1/2p5/4P3/1PN5/PBPP1PPP/R2QK1NR w KQkq - 0 7', 'd3'), ('e5', 'r4rk1/p2nqpbp/2p1p1p1/2p5/N2pP3/BP1P1Q1P/P1P2PP1/R3R1K1 w - - 4 15', 'Rf1'), ('Rac8', 'r4rk1/p2nqpbp/2p1p1p1/2p1P3/N2p4/BP1P1Q1P/P1P2PP1/R3R1K1 b - - 0 15', 'Nxe5'), ('h5', '2r2rk1/p2nqpbp/2p1p1p1/2p1P3/N2p4/BP1P2QP/P1P2PP1/R3R1K1 b - - 2 16', 'f5'), ('Rae1', '2r1rbk1/p2nqp2/2p1p1p1/2p1P2p/N2pRP2/BP1P2QP/P1P3P1/R5K1 w - - 3 19', 'Rxd4'), ('Qh4', '2rqrbk1/p2n1p2/2p1p1p1/2p1P2p/N2pRP2/BP1P1Q1P/P1P3P1/4R1K1 b - - 6 20', 'Nb6'), ('Kh2', '2r1rbk1/p2n1p2/2p1p1p1/2p1P2p/N2pRP1q/BP1P1Q1P/P1P3P1/4R1K1 w - - 7 21', 'f5'), ('gxf5', '2r1rbk1/p2n4/2p1p1p1/2p1Pp2/N2pRPPq/BP1P1Q2/P1P3K1/4R3 w - f6 0 25', 'exf6'), ('Kf7', '2r2bk1/p2n4/2p1p3/2p1Pp2/N2p1P2/BP1P4/P1P3K1/7R b - - 0 31', 'Kg7'), ('e7', '7k/p7/2N1Pn2/2b2p2/3p1P2/1P1P1K2/P1P5/8 w - - 1 42', 'b4'), ('Ne8', '8/p3P3/2Nb1nk1/5p2/1P3P2/P2P1K2/2P5/8 b - - 2 46', 'a6'), ('Qd3', 'r4rk1/1pq1ppbp/p1np1np1/8/2PNP3/2N1B2P/PP3PP1/R2QR1K1 w - - 2 13', 'b3'), ('Nd7', 'r4rk1/1pq1ppbp/p1np1np1/8/2PNP3/2NQB2P/PP3PP1/R3R1K1 b - - 3 13', 'Ne5'), ('c5', '1r3rk1/2qnpp1p/p1pp2pb/8/2PBPP2/2N3PP/PP2Q3/3RR1K1 b - - 0 19', 'e5'), ('Kh2', '1r3rk1/2qnppbp/p2p2p1/2p5/2P1PP2/2N3PP/PP2QB2/3RR1K1 w - - 2 21', 'Nd5'), ('Qb6', '1r3rk1/2qnppbp/p2p2p1/2p5/2P1PP2/2N3PP/PP2QB1K/3RR3 b - - 3 21', 'Bxc3'), ('Rd2', '1r3rk1/3nppbp/pq1p2p1/2p5/2P1PP2/2N3PP/PP2QB1K/3RR3 w - - 4 22', 'Nd5'), ('Rfe8', '1r3rk1/3nppbp/pq1p2p1/2p5/2P1PP2/2N3PP/PP1RQB1K/4R3 b - - 5 22', 'Bxc3'), ('Red1', '1r2r1k1/3nppbp/pq1p2p1/2p5/2P1PP2/2N3PP/PP1RQB1K/4R3 w - - 6 23', 'e5'), ('Qb4', '1r2r1k1/3nppbp/pq1p2p1/2p5/2P1PP2/2N3PP/PP1RQB1K/3R4 b - - 7 23', 'Bxc3'), ('Rc2', '1r2r1k1/3nppbp/p2p2p1/2p5/1qP1PP2/2N3PP/PP1RQB1K/3R4 w - - 8 24', 'Nd5'), ('Nb6', '1r2r1k1/3nppbp/p2p2p1/2p5/1qP1PP2/2N3PP/PPR1QB1K/3R4 b - - 9 24', 'Bxc3'), ('a5', '1r2r1k1/4ppbp/pn1p2p1/2p5/1qP1PP2/6PP/PPR1QB1K/1N1R4 b - - 11 25', 'Nd7'), ('b3', '1r2r1k1/4ppbp/1n1p2p1/p1p5/1qP1PP2/6PP/PPR1QB1K/1N1R4 w - - 0 26', 'Be1'), ('Nd2', '1r2r1k1/4ppbp/1n1p2p1/2p5/pqP1PP2/1P4PP/P1R1QB1K/1N1R4 w - - 0 27', 'Be1'), ('Bc3', '1r2r1k1/4ppbp/1n1p2p1/2p5/pqP1PP2/1P4PP/P1RNQB1K/3R4 b - - 1 27', 'axb3'), ('axb3', '1r2r1k1/4pp1p/1n1p2p1/2p5/1qP1PP2/1pb3PP/P1RNQ2K/3RB3 w - - 0 29', 'Nxb3'), ('Ra8', '1r2r1k1/4pp1p/1n1p2p1/2p5/1qP1PP2/1Pb3PP/2RNQ2K/3RB3 b - - 0 29', 'Bxd2'), ('Rb1', 'r3r1k1/4pp1p/1n1p2p1/2p5/1qP1PP2/1Pb3PP/2RNQ2K/3RB3 w - - 1 30', 'Qd3'), ('Reb8', 'r3r1k1/4pp1p/1n1p2p1/2p5/1qP1PP2/1Pb3PP/2RNQ2K/1R2B3 b - - 2 30', 'Ra1'), 
                ('f5', 'r5k1/1r1nppbp/3p2p1/2p5/2P1PPP1/qP1Q1N1P/2RB3K/1R6 w - - 1 35', 'Bc1'), ('Kf7', '6k1/3np3/3pNpp1/2p1b3/2P1P1P1/q6r/2RB4/5QK1 b - - 1 42', 'Bh2+'), ('Bc1', '8/3npk2/3pNpp1/2p1b3/2P1P1P1/q6r/2RB4/5QK1 w - - 2 43', 'Ng5+'), ('b6', 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', 'e5'), ('d5', 'rn1qkb1r/pbpppppp/1p3n2/8/4P3/2NP1N2/PPP2PPP/R1BQKB1R b KQkq - 0 4', 'e6'), ('exd5', 'rn1qkb1r/pbp1pppp/1p3n2/3p4/4P3/2NP1N2/PPP2PPP/R1BQKB1R w KQkq - 0 5', 'e5'), ('O-O', 'rn1qk2r/p1p2ppp/1p1bp3/3b4/5B2/3P1N2/PPP1BPPP/R2QK2R w KQkq - 2 9', 'Bg3'), ('bxc5', 'r2qk2r/pbpn1ppp/1p2p3/2P5/Q4b2/3P1N2/PP2BPPP/R4RK1 b kq - 0 12', 'Bh6'), ('Qe7', '1r1q1rk1/p1pn1ppp/4p3/2p5/5Q2/1P1P1B2/P4PPP/2R2RK1 b - - 0 16', 'Rb6'), ('Be4', '1r3rk1/p1pnqppp/4p3/2p5/5Q2/1P1P1B2/P4PPP/2R2RK1 w - - 1 17', 'Qxc7'), ('Rfc8', '1r3rk1/p1pnqppp/4p3/2p5/4BQ2/1P1P4/P4PPP/2R2RK1 b - - 2 17', 'Qd6'), ('Rfd1', '1rr3k1/p1pnqppp/4p3/2p5/4BQ2/1P1P4/P4PPP/2R2RK1 w - - 3 18', 'Bc6'), ('Nf6', '1rr3k1/p1pnqppp/4p3/2p5/4BQ2/1P1P4/P4PPP/2RR2K1 b - - 4 18', 'Qd6'), ('Qc6', '2r3k1/p1p2pp1/3qpn1p/1rp5/2R1Q3/1P1P1B2/P4PPP/3R2K1 w - - 4 24', 'Qe3'), ('Rb6', '2r3k1/p1p2pp1/2Qqpn1p/1rp5/2R5/1P1P1B2/P4PPP/3R2K1 b - - 5 24', 'Ra5'), ('Qa4', '2r3k1/p1p2pp1/1rQqpn1p/2p5/2R5/1P1P1B2/P4PPP/3R2K1 w - - 6 25', 'Qxc5'), ('a6', '2r3k1/p1p2pp1/1r1qpn1p/2p5/Q1R5/1P1P1B2/P4PPP/3R2K1 b - - 7 25', 'Ra6'), ('Qc3', '2r3k1/2p2pp1/p2qp2p/1rp5/1nR5/1P1P1B2/P1Q2PPP/3R2K1 w - - 6 29', 'Qb2'), ('R1b2', '6k1/2p2pp1/7p/1rpQ4/3p4/3P3P/5PPK/1r6 b - - 3 44', 'Rb6'), ('Qxc7', '3Q4/2p2ppk/7p/1rp5/3p4/3P3P/1r3PPK/8 w - - 6 46', 'Qd7'), ('Rfb2', '8/5ppk/7p/1rp1Q3/3p4/3P3P/5rPK/8 b - - 1 47', 'Rbb2'), ('Qe4+', '8/5ppk/7p/1rp1Q3/3p4/3P3P/1r4PK/8 w - - 2 48', 'Qf5+'), ('Kg8', '8/5pk1/6pp/1rp1Q3/3p4/1r1P3P/6PK/8 b - - 9 53', 'Kh7'), ('Qd5', '6k1/5p2/6pp/1rp1Q3/3p4/1r1P3P/6PK/8 w - - 10 54', 'Qe8+'), ('Kg7', '6k1/5p2/6pp/1rpQ4/3p4/1r1P3P/6PK/8 b - - 11 54', 'Rxd3'), ('Qd7', '8/5pk1/6pp/1rpQ4/3p4/1r1P3P/6PK/8 w - - 12 55', 'Qe5+'), ('Kg8', '8/3Q1pk1/6pp/1rp5/3p4/1r1P3P/6PK/8 b - - 13 55', 'Rb6'), ('Qd8+', '6k1/3Q1p2/6pp/1rp5/3p4/1r1P3P/6PK/8 w - - 14 56', 'Qe8+'), ('Kg8', '8/3Q1pk1/6pp/1rp5/3p4/1r1P3P/6PK/8 b - - 17 57', 'Rb6'), ('Qc6', '6k1/3Q1p2/6pp/1rp5/3p4/1r1P3P/6PK/8 w - - 18 58', 'Qe8+'), ('Kg7', '6k1/5p2/2Q3pp/1rp5/3p4/1r1P3P/6PK/8 b - - 19 58', 'Rb8'), ('Qd5', '8/5pk1/2Q3pp/1rp5/3p4/1r1P3P/6PK/8 w - - 20 59', 'Qd7'), ('Rd2', '6k1/5p2/6pp/2pQ4/3p4/1r1P3P/1r4PK/8 b - - 33 65', 'Rxd3'), ('Qe5', '6k1/5p2/6pp/2pQ4/3p4/1r1P3P/3r2PK/8 w - - 34 66', 'Qxb3'), ('Rdxd3', '6k1/5p2/6pp/2p1Q3/3p4/1r1P3P/3r2PK/8 b - - 35 66', 'Rbb2'), ('Nxd5', 'r1bqr1kb/pp2pp2/2np1npB/2pN3p/2P1P2P/3P1N2/PP1QBPP1/R3K2R b KQ - 7 11', 'a6'), ('Ng5', 'r1bqr1kb/pp2pp2/3p2pB/2pP3p/2Pn3P/3P1N2/PP1QBPP1/R3K2R w KQ - 1 13', 'Nxd4'), ('Bg7', 'r3r1kb/pp2pp2/3p2pB/q1pP1bNp/2P4P/3P1P2/PP2Q1P1/R4K1R b - - 0 16', 'Qb6'), 
    ('Qf3', 'r3r3/pp1bppk1/3p2p1/q1pP2N1/2P3PP/3P4/PP2Q3/R4K1R w - - 1 20', 'h5'), ('Ne6+', 'r3r3/pp1bp1k1/3p1pp1/q1pP2N1/2P3PP/3P1Q2/PP6/R4K1R w - - 0 21', 'Ne4'), ('Rh8', 'r3r3/pp2p1k1/3pPpp1/q1p5/2P3PP/3P1Q2/PP6/R4K1R b - - 0 22', 'Qd2'), ('Qa4', '4r2r/pQ2p1k1/3pPpp1/q1p5/2P3PP/3P4/PP2K3/R6R b - - 2 24', 'd5'), ('Qa4', '4r2r/pQ2p1k1/3pPpp1/q1p5/2P3PP/3PK3/PP6/R6R b - - 6 26', 'd5'), ('b3', '4r2r/pQ2p1k1/3pPpp1/2p5/q1P3PP/3PK3/PP6/R6R w - - 7 27', 'h5'), ('Rc2', '4r2r/pQ2p1k1/3pPpp1/q1p5/2P3PP/1P1PK3/P6R/7R w - - 7 31', 'Rc1'), ('Kf8', '4r2r/pQ2p1k1/3pPpp1/q1p5/2P3PP/1P1PK3/P1R5/7R b - - 8 31', 'Rxh4'), ('Kb1', 'rnb1k2r/1p2bppp/p2ppn2/q5B1/3NP3/2N2Q2/PPP2PPP/2KR1B1R w kq - 4 9', 'Bd2'), ('Nh4', 'r3kb1r/pp1q1ppp/2np1nb1/2p1p3/4P1P1/2P2N1P/PPBP1P2/RNBQR1K1 w kq - 3 10', 'd4'), ('a6', 'r3k2r/pp1qbppp/2np1nb1/2p1p3/4P1PN/N1P4P/PPBP1P2/R1BQR1K1 b kq - 6 11', 'h5'), ('Bxe4', 'r3k2r/1pq1bppp/p1np1nb1/2p1p3/4P1PN/2P1N2P/PPBP1P2/R1BQR1K1 b kq - 3 13', 'Qd7'), ('Rxe4', 'r3k2r/1p1qbppp/p1np4/2pNp3/4n1PN/2P4P/PP1P1P2/R1BQR1K1 w kq - 2 16', 'Nxe7'), ('Qxa8', 'N2qk2r/1p3ppp/p1np4/2p1p3/4R1Pb/2P4P/PP1P1P2/R1BQ2K1 b k - 0 18', 'O-O'), ('O-O', 'q3k2r/1p3ppp/p1np4/2p1p3/3PR1Pb/2P4P/PP3P2/R1BQ2K1 b k - 0 19', 'd5'), ('d5', 'q4rk1/1p3ppp/p1np4/2p1p3/3PR1Pb/2P4P/PP3P2/R1BQ2K1 w - - 1 20', 'dxc5'), ('c4', 'q4rk1/1p2nppp/p2p4/2pPp3/4R1Pb/2P4P/PP3P2/R1BQ2K1 w - - 1 21', 'g5'), ('b5', 'q4rk1/1p2nppp/p2p4/2pPp3/2P1R1Pb/7P/PP3P2/R1BQ2K1 b - - 0 21', 'f5'), ('b3', 'q4rk1/4nppp/p2p4/1ppPp3/2P1R1Pb/7P/PP3P2/R1BQ2K1 w - - 0 22', 'b4'), ('Ng6', 'q4rk1/4nppp/p2p4/1ppPp3/2P1R1Pb/1P5P/P4P2/R1BQ2K1 b - - 0 22', 'f5'), ('a4', 'q4rk1/5ppp/p2p2n1/1ppPp3/2P1R1Pb/1P5P/P4P2/R1BQ2K1 w - - 1 23', 'cxb5'), ('Rf3', '5qk1/6pp/p2p2n1/2pPpr2/PpP1R2b/1P2B2P/4QP2/R5K1 b - - 3 27', 'Bg5'), ('Nf4+', '5qk1/6pp/p2p1rn1/2pPp3/PpP1R2b/1P2B2P/4QPK1/5R2 b - - 7 29', 'Rf5'), ('h6', '6k1/6pp/p2p4/2pPp3/PpP3Pb/1P6/5PK1/5R2 b - - 0 33', 'Bg5'), ('Bg5', '6k1/6p1/p2p3p/2pP4/PpP2RPb/1P6/6K1/8 b - - 0 35', 'a5'), ('Bc5', 'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2', 'Nc6'), ('Bb5', 'rnbqk1nr/pppp1ppp/8/2b1p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3', 'Nxe5'), ('Re1', 'r2q1rk1/pppbnppp/1bnp4/1B4B1/3PP3/2N2N2/PP3PPP/R2Q1RK1 w - - 5 10', 'h3'), ('Qc8', 'r2q1rk1/pppbnpp1/1bnp3p/1B6/3PP2B/2N2N2/PP3PPP/R2QR1K1 b - - 1 11', 'Bg4'), ('Nd5', '2rq1rk1/3nbpp1/p2pbn2/1p2p1B1/4P1Pp/PNN2P1P/1PPQ4/1K1R1B1R b - - 1 15', 'Nb6'), ('Bxe7', '2rq1rk1/3nbpp1/p2pb3/1p1np1B1/4P1Pp/PNN2P1P/1PPQ4/1K1R1B1R w - - 2 16', 'exd5'), ('Rfc8', '5rk1/4qpp1/p2pb3/1pr1p3/4PPPp/P3Q2P/1PP5/1K1R1B1R b - - 0 20', 'exf4'), ('Bc6', '2r3k1/3bqpp1/p2p4/1pr1pP2/4P1Pp/P3Q2P/1PPR4/1K3B1R b - - 2 22', 'a5'), ('g5', '2r3k1/4qpp1/p1b5/1prppP2/4P1Pp/P3Q2P/1PPR4/1K3BR1 w - - 0 24', 'f6'), ('Qc7', '2r3k1/4qpp1/p1b5/1pr1pPP1/3pP2p/P4Q1P/1PPR4/1K3BR1 b - - 1 25', 'g6'), ('Nxe4', 'rnbqkb1r/pp2pppp/3p1n2/2p5/4P3/2P2N1P/PP1P1PP1/RNBQKB1R b KQkq - 0 4', 'Nc6'), ('g6', 'r1bqkbnr/1p1ppppp/p7/2p5/4P3/2N2N2/PPPP1PPP/R1BQK2R b KQkq - 1 6', 'b5'), 
    ('e6', 'r1bqkb1r/1p1ppp1p/p5p1/4P2n/3Q4/2N2N2/PPP2PPP/R1B1K2R w KQkq - 1 10', 'Nd5'), ('Bg7', 'r1bqkb1r/1p1ppp1p/p3P1p1/7n/3Q4/2N2N2/PPP2PPP/R1B1K2R b KQkq - 0 10', 'f6'), ('Nxd5', 'r1bq2kr/1p4bp/p3pnp1/3pN1B1/2Q5/2N5/PPP2PPP/2KR3R w - - 0 16', 'Qd3'), ('c4', 'rn1qkb1r/ppp1pppp/8/3n1b2/3P4/5N2/PPP2PPP/RNBQKB1R w KQkq - 2 5', 'Bd3'), ('Nb6', 'rn1qkb1r/ppp1pppp/8/3n1b2/2PP4/5N2/PP3PPP/RNBQKB1R b KQkq - 0 5', 'Nb4'), ('N8d7', 'rn1qk2r/ppp1bppp/1n2p3/5b2/2PP4/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 3 8', 'O-O'), ('c5', 'r2qr1k1/p2n1ppp/PppBpn2/5b2/2PP4/5N2/1P2BPPP/R2Q1RK1 w - - 1 16', 'h3'), ('Nf8', 'r2qr1k1/p2n1ppp/PppBpn2/2P2b2/3P4/5N2/1P2BPPP/R2Q1RK1 b - - 0 16', 'Ne4'), ('Bxe4', '2rqrnk1/p4ppp/PppBp3/2P1Nb2/3Pn3/5B2/1P3PPP/R2Q1RK1 w - - 5 19', 'Bxf8'), ('Nxg6', '2rqrnk1/p4ppp/PppBp1b1/2P1N2Q/3P4/8/1P3PPP/R4RK1 w - - 2 21', 'Qf3'), ('Qf3', '2rqr1k1/p4ppp/P1pBp1n1/1pP4Q/3P4/8/1P3PPP/R3R1K1 w - - 0 23', 'Re4'), ('Red8', '2r1r1k1/p4ppp/P1p1p3/1pP1Bn2/3PR3/8/1P3PPP/R5K1 b - - 2 27', 'h5'), ('Re8', '2rr2k1/p4ppp/P1pBp3/1pPn4/3PR1P1/8/1P3P1P/4R1K1 b - - 4 30', 'Nf6'), ('Nb4', '2r1r1k1/p4ppp/P1pBp3/1pPn4/3PRPP1/8/1P5P/4R1K1 b - - 0 31', 'Nf6'), ('b4', '2r3k1/R5pp/2pB4/1pP5/3P2P1/1P6/7P/2n3K1 w - - 1 40', 'Be5'), ('Be5', '2r3k1/R5pp/2pB4/1pP5/1P1P2P1/3n4/7P/6K1 w - - 1 41', 'Re7'), ('Nxb4', '2r3k1/R5pp/2p5/1pP1B3/1P1P2P1/3n4/7P/6K1 b - - 2 41', 'Nxe5'), ('Bc4', 'rnbqkb1r/1p3pp1/p2ppn1p/8/3NP1P1/2N4P/PPP2P2/R1BQKB1R w KQkq - 0 8', 'h4'), ('Nc6', 'rnbqkb1r/1p3pp1/p2ppn1p/8/2BNP1P1/2N4P/PPP2P2/R1BQK2R b KQkq - 1 8', 'b5'), ('h4', 'r1bqkb1r/5pp1/p1pppn1p/8/2B1P1P1/2N4P/PPP2P2/R1BQK2R w KQkq - 0 10', 'Bb3'), ('d4', 'r1bqkb1r/5pp1/p1p1pn1p/3p4/4P1PP/1BN5/PPP2P2/R1BQK2R b KQkq - 1 11', 'Bb4'), ('Nxd4', 'r1bqkb1r/5pp1/p1p1p2p/8/3pn1PP/1B6/PPP1NP2/R1BQK2R w KQkq - 0 13', 'Qxd4'), ('Bc5', 'r1bqkb1r/5pp1/p1p1p2p/8/3Nn1PP/1B6/PPP2P2/R1BQK2R b KQkq - 0 13', 'c5'), ('Qf3', 'r2qk2r/1b3pp1/p1p1p2p/2b5/3Nn1PP/1B2B3/PPP2P2/R2QK2R w KQkq - 3 15', 'Qd3'), ('Rb8', 'r2qk2r/1b3pp1/p1p1p2p/8/3bQ1PP/1B2B3/PPP2P2/R3K2R b KQkq - 0 16', 'Qa5+'), ('Qe7', 'r1bqk1nr/pppp1ppp/2nb4/1B2p3/4P3/5N2/PPPP1PPP/RNBQ1RK1 b kq - 5 4', 'Nge7'), ('Bxc6', '2kr2nr/pbppqpp1/1pnb3p/1B2p3/P2PP3/2P2N2/1P3PPP/RNBQR1K1 w - - 0 9', 'd5'), ('exd4', '2kr2nr/pbp1qpp1/1ppb3p/P3p3/3PP3/2P2N2/1P3PPP/RNBQR1K1 b - - 0 10', 'g5'), ('Ne5', '2kr3r/1bp1qpp1/1pp2n1p/8/3PP3/5N2/1P1Q1PPP/RN2R1K1 w - - 0 15', 'Qc2'), ('Nd7', '2kr3r/1bp1qpp1/1pp2n1p/4N3/3PP3/8/1P1Q1PPP/RN2R1K1 b - - 1 15', 'c5'), ('Nf6', '2kr3r/1bpnqpp1/1pp4p/8/2NPP3/8/1P1Q1PPP/RN2R1K1 b - - 3 16', 'Rhe8'), 
    ('e5', '2krr3/1bp1qpp1/1pp2n1p/8/2NPP3/2N5/1P1Q1PPP/R3R1K1 w - - 6 18', 'f3'), ('f5', '2krr3/1bp1qpp1/1pp4p/3nP3/2NPN3/8/1P1Q1PPP/R3R1K1 b - - 2 19', 'Qb4'), ('gxf6', '2krr3/1bp1q1p1/1pp2P1p/3n4/2NPN3/8/1P1Q1PPP/R3R1K1 b - - 0 20', 'Qf8'), ('dxe5', '2kr1b1r/ppp2ppp/2n5/3qp3/3P2b1/2P2N2/PP2BPPP/R1BQK2R w KQ - 2 9', 'O-O'), ('cxb4', 'r1bqk1nr/pp1p1pbp/2n1p1p1/2p5/1P2PP2/P1N2N2/2PP2PP/R1BQKB1R b KQkq - 0 6', 'b6'), ('Na5', 'r2q1rk1/2p1bppp/p1np1n2/1p2p3/3PP1b1/1BP2N2/PP1N1PPP/R1BQR1K1 b - - 2 10', 'exd4'), ('Rf6', 'r4rk1/3nq1p1/p2p2pp/np1Pp3/2p1P1Q1/2P5/PPB2PPP/R1B1R1K1 b - - 1 19', 'g5'), ('f4', '5rk1/1n1nq1p1/p2p1rpp/1p1Pp3/2p1P1Q1/2P1B3/PPB2PPP/R4RK1 w - - 6 22', 'b4'), ('Nd3', '5rk1/6p1/5qpp/1ppPn3/2p1P3/2P1Q3/1PB3PP/R5K1 b - - 1 29', 'h5'), ('Qf4', '5rk1/6p1/5qpp/1p1PP3/2p5/2PpQ2P/1P4P1/R5K1 b - - 0 32', 'Qf5'), ('Nd5', '1r1q1rk1/4bppp/p1bp1n2/2p1p3/2P1P1P1/1PN2N1P/PB2QP2/R3K2R w KQ - 1 14', 'Rd1'), ('g5', '1r1q1rk1/5ppp/2bp1b2/2p1p3/p1P1P1PP/1P3N2/PB2QP2/R3K2R w KQ - 0 17', 'Qe3'), ('g6', 'r2qkbnr/pp1b1ppp/2n1p3/2ppP3/3P4/2PB1N2/PP3PPP/RNBQK2R b KQkq - 4 6', 'cxd4'), ('h5', 'r2qk1nr/pp1b1pbp/2n1p1p1/3pP3/3P3P/3B1N2/PP3PP1/RNBQ1RK1 b kq - 0 9', 'f6'), ('Rb8', 'r2q1rk1/pp1bnpb1/2nNp1p1/3pP2p/3P3P/3B1N2/PP3PP1/R1BQ1RK1 b - - 5 12', 'f6'), ('Ng5', '1r1q1rk1/pp1bnpb1/2nNp1p1/3pP2p/3P3P/3B1N2/PP3PP1/R1BQ1RK1 w - - 6 13', 'Re1'), ('Nc8', '1r1q1rk1/pp1bnpb1/2nNp1p1/3pP1Np/3P3P/3B4/PP3PP1/R1BQ1RK1 b - - 7 13', 'f6'), ('Nxf7', '1rnq2k1/pp1b1rb1/2n1p1p1/3pP1Np/3P3P/3B4/PP3PP1/R1BQ1RK1 w - - 0 15', 'Bxg6'), ('Qxh4', '1rnq2k1/pp1b2b1/2n1p1B1/3pP2p/3P3P/5Q2/PP3PP1/R1B2RK1 b - - 0 17', 'Be8'), ('Be2', '2rqk2r/3nbpp1/p2pbn2/1p2p2p/4P3/1NN1BP1P/PPPQ2P1/1K1R1B1R w k - 0 13', 'Bd3'), ('b4', '2rqk2r/3nbpp1/p2pbn2/1p2p2p/4P3/1NN1BP1P/PPPQB1P1/1K1R3R b k - 1 13', 'Nb6'), ('g4', '2rqk2r/3nbpp1/p2p4/3Ppb1p/1p6/1N2BP1P/PPPQB1P1/1K1R3R w k - 1 16', 'Bd3'), ('c5', 'rnbqr1k1/ppp2pbp/3p2p1/7n/2PNP3/2N1BP2/PP2B1PP/R2Q1RK1 b - - 2 10', 'Nc6'), ('Nb3', 'rnbqr1k1/pp3pbp/3p2p1/2p4n/2PNP3/2N1BP2/PP2B1PP/R2Q1RK1 w - - 0 11', 'Ndb5'), ('Nf6', 'r1bqr1k1/pp3pbp/2np2p1/2p4n/2P1P3/1NN1BP2/PP1QB1PP/R4RK1 b - - 3 12', 'Be6'), ('Nb5', 'r1bqr1k1/pp3pbp/2np1np1/2p5/2P1P3/1NN1BP2/PP1QB1PP/R4RK1 w - - 4 13', 'Rad1'), ('Nd4', 'r1bq2k1/1p3pbp/p1nNrnp1/2p5/2P1P3/1N2BP2/PP1QB1PP/R2R2K1 b - - 0 15', 'b6'), ('Bxd4', '2rq2k1/1p3pbp/p3rnp1/8/2PpP3/4BP2/PP1QB1PP/R2R2K1 w - - 0 18', 'Qxd4'), ('Rd6', '2rq2k1/1p3pbp/p3rnp1/8/2PBP3/5P2/PP1QB1PP/R2R2K1 b - - 0 18', 'Nxe4'), ('Qe3', '2rq2k1/1p3pbp/p2r1np1/8/2PBP3/5P2/PP1QB1PP/R2R2K1 w - - 1 19', 'e5'), ('Qa5', '2rq2k1/1p3pbp/p2r1np1/8/2PBP3/4QP2/PP2B1PP/R2R2K1 b - - 2 19', 'Ng4'), 
    ('Bg4', '2B2bk1/1p3p1p/p1q3p1/4P3/5P2/P3n2P/1P3QP1/R5K1 w - - 0 31', 'Bxb7'), ('hxg4', '5bk1/1p3p1p/p1q3p1/4P3/5Pn1/P6P/1P3QP1/R5K1 w - - 0 32', 'Qd2'), ('Qc6', 'r3r1k1/1pq1ppbp/p4np1/2ppBb2/Pn3P2/NP2PN1P/2PPB1P1/R2Q1RK1 b - - 2 13', 'Qb6'), ('Rc1', 'r3r1k1/1p2ppbp/p1q2np1/2ppBb2/Pn3P2/NP2PN1P/2PPB1P1/R2Q1RK1 w - - 3 14', 'g4'), ('d4', 'r3r1k1/1p2ppbp/p3qnp1/2ppBb2/Pn3P2/NP2PN1P/2PPB1P1/2RQ1RK1 w - - 5 15', 'g4'), ('Bxh3', 'r3r1k1/1p2ppbp/p3qnp1/2ppBb2/Pn1P1P2/NP2PN1P/2P1B1P1/2RQ1RK1 b - - 0 15', 'Na2'), ('Bxf6', 'r3r1k1/1p2ppbp/p3qnp1/2ppB3/Pn1P1P2/NP2PN1b/2P1B1P1/2RQ1RK1 w - - 0 16', 'Ng5'), ('Bxf6', 'r3r1k1/1p2ppbp/p3qBp1/2pp4/Pn1P1P2/NP2PN1b/2P1B1P1/2RQ1RK1 b - - 0 16', 'exf6'), ('Qxf4', 'r3r1k1/1p2pp1p/p4bp1/2pp4/Pn1P1P2/NP2qN1P/2P1B1K1/2RQ1R2 b - - 1 18', 'Na2'), ('Ne5', 'r3r1k1/1p2pp1p/p1n2bp1/2pp4/P2P1q2/NPP2N1P/4B1K1/2RQ1R2 w - - 1 20', 'dxc5'), ('Bxe5', 'r3r1k1/1p2pp1p/p4bp1/2ppP1q1/P7/NPP4P/4B3/2RQ1R1K b - - 0 22', 'Qxe5'), ('Bf3', '3rr1k1/1p2pp1p/p5p1/2p5/P1N5/1PP3bP/4B3/2R2R1K w - - 0 27', 'a5'), ('b4', '1b2r3/4ppkp/6p1/1ppN4/8/1PPr1B1P/6K1/2R2R2 w - - 6 32', 'Rfd1'), ('Rfe1', '1b2r3/4ppkp/6p1/1p1N4/1Pp5/2Pr1B1P/6K1/2R2R2 w - - 0 33', 'Rcd1'), ('Ne3', '1b2r3/5pkp/6p1/1p1Np3/1Pp5/2Pr1B1P/6K1/2R1R3 w - - 0 34', 'Be4'), ('f3', 'r1bqkb1r/5ppp/p1np1n2/1p1Np3/4P3/N7/PPP2PPP/R1BQKB1R w KQkq - 2 9', 'c4'), ('Nxe4', 'r1bqkb1r/5ppp/p1np1n2/1p1Np3/4P3/N4P2/PPP3PP/R1BQKB1R b KQkq - 0 9', 'Nxd5'), ('Ke2', 'r1b1kb1r/5ppp/p1np4/1p1Np3/4P2q/N7/PPP3PP/R1BQKB1R w KQkq - 1 11', 'Kd2'), ('Qxe4+', 'r1b1kb1r/5ppp/p1np4/1p1Np3/4P2q/N7/PPP1K1PP/R1BQ1B1R b kq - 2 11', 'Bg4+'), ('Be3', 'r1b1kb1r/5ppp/p1np4/1p1Np3/4q3/N7/PPP1K1PP/R1BQ1B1R w kq - 0 12', 'Kf2'), ('Nd4+', 'r1b1kb1r/5ppp/p1np4/1p1Np3/4q3/N3B3/PPP1K1PP/R2Q1B1R b kq - 1 12', 'Bg4+'), ('Bxd4', 'r1b1kb1r/5ppp/p2p4/1p1qp3/3n4/N3B3/PPP2KPP/R2Q1B1R w kq - 0 14', 'c3'), ('Bg7', 'r2qkb1r/1bpnpp2/p2p1npp/1p6/3PP3/2NBBP2/PPPQN1PP/R3K2R b KQkq - 3 9', 'c5'), ('Nf4', 'r2qk2r/1bpnppb1/p2p1npp/1p6/3PP3/2NBBP2/PPPQN1PP/R3K2R w KQkq - 4 10', 'a4'), ('e5', 'r2qk2r/1b1nppb1/p2p1npp/1pp5/3PPN2/2NBBP2/PPPQ2PP/R3K2R w KQkq - 0 11', 'dxc5'), ('g5', '2r1r1k1/1b2ppb1/p1n2npp/1pB5/2p2N2/2N2P2/PPPRB1PP/2KR4 b - - 8 19', 'e6'), ('e6', '2r1r1k1/1b2ppb1/p1n2n1p/1pBN2p1/2p5/2N2P2/PPPRB1PP/2KR4 b - - 1 20', 'Nd7'), ('Nb6', '2r1r1k1/1b3pb1/p1n1pn1p/1pBN2p1/2p5/2N2P2/PPPRB1PP/2KR4 w - - 0 21', 'Nxf6+'), ('Rcd8', '2r1r1k1/1b3pb1/pNn1pn1p/1pB3p1/2p5/2N2P2/PPPRB1PP/2KR4 b - - 1 21', 'Rb8'), ('Rxd8', '3Rr1k1/1b3pb1/pNn1pn1p/1pB3p1/2p5/2N2P2/PPP1B1PP/2KR4 b - - 0 22', 'Nxd8'), ('Be7', '3n2k1/1b3pb1/pN2pn1p/1pB3p1/2p5/2N2P2/PPP1B1PP/2K5 w - - 0 24', 'a4'), ('Nd5+', '8/1b3k2/pNn1pn1p/1pB2pp1/2p5/2P1KPP1/P1P1B2P/8 b - - 0 30', 'e5'), ('Ke6', '8/1b3k2/p1n4p/1pBp1pp1/2p2P2/2P1K1P1/P1P1B2P/8 b - - 0 32', 'g4'), ('Bf1', '4b3/8/p3k3/1p1p1p2/2pBnKp1/P1P3P1/2P1B2P/8 w - - 9 41', 'Ke3'), ('Bg6', '4b3/8/p3k3/1p1p1p2/2pBnKp1/P1P3P1/2P4P/5B2 b - - 10 41', 'Nd2'), ('h3', '8/8/4k1b1/pp1p1p2/2pBnKp1/P1P3P1/2P3BP/8 w - - 0 43', 'Ke3'), ('gxh3', '8/8/4k1b1/pp1p1p2/2pBnKp1/P1P3PP/2P3B1/8 b - - 0 43', 'Nd2'), ('Bg2', '8/8/4k1b1/pp1p1p2/2pB1K2/P1P3PB/2Pn4/8 w - - 1 45', 'Bc5'), ('Nc1', 'r1bq1rk1/1pp2pbp/n2p1np1/p3p3/2PPP3/2N1BP2/PP1QN1PP/R3KB1R w KQ - 2 9', 'g4'), ('Nb4', 'r1bq1rk1/1pp2pbp/n2p1np1/p3p3/2PPP3/2N1BP2/PP1Q2PP/R1N1KB1R b KQ - 3 9', 'exd4'), ('Be2', 'r1bq1rk1/1pp2pbp/3p1np1/p3p3/1nPPP3/2N1BP2/PP1Q2PP/R1N1KB1R w KQ - 4 10', 'd5'), ('Ne8', 'r1bq1rk1/1pp2pbp/3p1np1/p3p3/1nPPP3/2N1BP2/PP1QB1PP/R1N1K2R b KQ - 5 10', 'exd4'), ('O-O', 'r1bqnrk1/1pp3bp/n2p2p1/p2Ppp2/2P1P3/P1N1BP2/1P1QB1PP/R1N1K2R w KQ - 1 13', 'Nd3'), ('Rxa3', 'r1bqnrk1/1pp3bp/6p1/2pPp3/2P1Pp2/PNN2P2/3QB1PP/1R3RK1 b - - 0 18', 'Qe7'), ('Qd6', '2bqnrk1/rpp3bp/8/2NPp1p1/2P1Pp2/2N2P2/1Q2B1PP/1R1R2K1 b - - 3 21', 'Kh8'), ('h5', '2b1nrk1/rpp3bp/3q4/3Pp1p1/2P1Pp2/2NN1P2/1Q2B1PP/1R1R2K1 b - - 5 22', 'Qg6'), ('e5', 'r1b1k2r/p4ppp/2p1pn2/q2p4/1b2P3/2NBB3/PPPQ1PPP/R3K2R w KQkq - 0 10', 'exd5'), ('f4', 'r1b1k2r/p2n1ppp/2p1p3/q2pP3/1b6/2NBB3/PPPQ1PPP/R3K2R w KQkq - 1 11', 'a3'), ('Nxh4', 'r1bq1rk1/3pbppp/p1n1p1n1/1p6/4P2P/2NB1N2/PPPBQPP1/2KR3R b - - 0 11', 'Nge5'), ('Re8+', 'b4k2/3pR3/p4B2/1p2p3/3n4/1PNB2r1/PKP5/8 w - - 9 37', 'Rxd7'), ('Kf7', 'b3Rk2/3p4/p4B2/1p2p3/3n4/1PNB2r1/PKP5/8 b - - 10 37', 'Kxe8'), ('Nxd4+', '8/8/R2pk3/1N2p3/3n4/1P1r4/PKP5/8 w - - 0 42', 'Rxd6+'), ('Ra5', '8/8/R2pk3/4p3/3r4/1P6/PKP5/8 w - - 0 43', 'a4'), ('Re4', '8/8/3pk3/R3p3/3r4/1P6/PKP5/8 b - - 1 43', 'e4'), ('Ra4', '8/8/3pk3/R3p3/4r3/1P6/PKP5/8 w - - 2 44', 'a4'), ('Rf4', '8/8/3pk3/4p3/R3r3/1P6/PKP5/8 b - - 3 44', 'Rxa4'), ('c3', '8/8/3pk3/8/5p2/1P6/PKP5/8 w - - 0 46', 'Kc3'), ('f3', '8/8/3p4/5k2/5p2/1PP5/P1K5/8 b - - 2 47', 'Kg4'), ('a4', 'r1bq1rk1/1p1pnpbp/2n1p1p1/p1p5/2P5/P1NP1NP1/1P2PPBP/1RBQ1RK1 b - - 0 9', 'b6'), ('Nd2', 'r1bq1rk1/1p2npbp/2n1p1p1/2pp4/N1P5/P2P1NP1/1P2PPBP/1RBQ1RK1 w - - 0 11', 'Nxc5'), ('Qd6', 'r1bq1rk1/1p2npbp/2n1p1p1/2pp4/N1P5/P2P2P1/1P1NPPBP/1RBQ1RK1 b - - 1 11', 'Qa5'), ('g5', 'r1bqkb1r/1p3ppp/p2ppn2/2n5/3NP1P1/1BN5/PPP2P1P/R1BQK2R w KQkq - 1 9', 'Qe2'), ('Be3', 'r3k2r/1p2b1pp/p3p3/3pp1P1/4n2P/8/PPPBBP2/2KR3R w kq - 0 20', 'Be1'), ('d4', 'r3kr2/1p2b1pp/p3p3/3pp1P1/7P/4BPn1/PPP1B2R/2KR4 b q - 2 22', 'Nxe2+'), ('exf4', 'r3kr2/1p4pp/p2bp3/4p1P1/3p1P1P/8/PPPBR3/2KR4 b q - 0 25', 'Rc8'), ('Rac8+', 'r4r2/1p1k2pp/p2b4/6P1/4R2P/3P1p2/PP1B4/2K2R2 b - - 1 29', 'Rae8'), ('Bf6', '5r2/1p1k3p/p2b2p1/5rP1/4R2P/P1BP1p2/1P6/3K1R2 w - - 1 33', 'Bb4'), ('Rc8', '5r2/1p1k3p/p2b1Bp1/5rP1/4R2P/P2P1p2/1P6/3K1R2 b - - 2 33', 'Re8'), ('Rf4', '2r5/1p1k3p/p2b1Bp1/5rP1/7P/P2PRp2/1P6/3K1R2 b - - 4 34', 'f2'), ('Bg3', '2r5/1p1k3p/p2b1Bp1/6P1/4P2P/P4p2/1P6/3K1R2 b - - 0 36', 'Rc4'), ('Bxh4', '2r5/1p1k3p/p4Bp1/6P1/4P2P/P4Rb1/1P6/3K4 b - - 0 37', 'Bd6'), ('Bc3', '2r5/1p1k3p/p4Bp1/6P1/4P2b/P4R2/1P6/3K4 w - - 0 38', 'Rh3'), ('Ke6', '2r5/1p1k3p/p5p1/6P1/4P2b/P1B2R2/1P6/3K4 b - - 1 38', 'Re8'), ('Bf6', '2r5/1R6/p3k1p1/6b1/4P3/P1B5/1P6/3K4 b - - 0 42', 'Rd8+'), ('dxc4', 'r1bqkb1r/pp2pp1p/2n2np1/3p2B1/2PP4/2N2N2/PP3PPP/R2QKB1R b KQkq - 1 7', 'Be6'), ('Bxf6', 'r1bqkb1r/pp2pp1p/2n2np1/6B1/2pP4/2N2N2/PP3PPP/R2QKB1R w KQkq - 0 8', 'Bxc4'), ('f3', 'r3r1k1/pp3pbp/3n1pp1/3P4/6b1/1BN5/PP1N1PPP/R3R1K1 w - - 7 17', 'Nce4'), ('Rb8', 'r5k1/pp1b1pbp/3N2p1/3P1p2/8/1B3P2/PP4PP/4R1K1 b - - 0 21', 'Bf8'), ('Re2', '1r4k1/pp1b1pbp/3N2p1/3P1p2/8/1B3P2/PP4PP/4R1K1 w - - 1 22', 'Re7'), ('O-O-O', 'r1b2rk1/pp2ppbp/2n3p1/3q4/3N4/4BP2/PPPQ2PP/R3KB1R w KQ - 0 11', 'Nxc6'), ('Qd3+', '2rr2k1/pp2p1Bp/4p1p1/6Q1/1n2K2P/2P2P2/1P1q2P1/5B1R b - - 2 20', 'Qe1+'), ('c6', 'rnbqkb1r/ppp1pppp/1n6/4P3/2PP4/8/PP4PP/RNBQKBNR b KQkq - 0 6', 'Nc6'), ('Qb6+', 'r1bq1rk1/pp2ppbp/3p2p1/1B2n1B1/4PP2/2N4P/PPP3P1/R2Q1RK1 b - - 0 12', 'a6'), ('Na4', 'r1b1r1k1/p4pbp/2pB2p1/8/4PP2/2N4P/PqP3PK/R2Q1R2 w - - 0 17', 'Rf3'), ('Ba6', 'r1b1r1k1/p4p1p/2pB2p1/8/N3PP2/7P/P1P3PK/R7 b - - 0 19', 'Rxe4'), ('Na6', 'r3r1k1/pR3p1p/2pB2p1/2NbP3/P4P2/7P/2P3PK/8 w - - 5 25', 'a5'), ('Red8', 'r3r1k1/pR3p1p/N1pB2p1/3bP3/P4P2/7P/2P3PK/8 b - - 6 25', 'c5'), ('Nc7', 'r2r2k1/pR3p1p/N1pB2p1/3bP3/P4P2/7P/2P3PK/8 w - - 7 26', 'Nc5'), ('Bc6', 'r4k2/5p2/1B4p1/PN1bP2p/5P2/7P/2P3PK/8 b - - 3 33', 'Rc8'), ('Nd6', 'r4k2/5p2/1Bb3p1/PN2P2p/5P2/7P/2P3PK/8 w - - 4 34', 'c4'), ('h4', '5r2/4k3/1BbN2p1/P1P1P2p/8/7P/6PK/8 w - - 1 38', 'Kg3'), ('Ra4', '8/P7/1Bb1k1p1/2P1P2p/2N4P/7K/r7/8 b - - 2 42', 'Bd5'), ('Rxa5', 'b7/P7/1BP1k1p1/N3P2p/r6P/7K/8/8 b - - 0 44', 'Kxe5'), ('Bc7', '8/P7/2b1k1p1/B3P2p/7P/7K/8/8 w - - 0 46', 'Bc3'), ('Ke6', '8/P1B5/2b3p1/4Pk1p/7P/6K1/8/8 b - - 3 47', 'g5'), ('a8=Q', '1B6/P7/4k1p1/4P1Kp/4b2P/8/8/8 w - - 12 52', 'Bd6'), ('Kf6', '8/2Bk4/8/4P1Kp/7P/8/8/3b4 w - - 11 59', 'Bb8'), ('Kd8', '8/2k5/4PK2/7p/7P/8/8/3b4 b - - 0 60', 'Kd6'), ('e7+', '3k4/8/4PK2/7p/7P/8/8/3b4 w - - 1 61', 'Kf7'), ('Bg4', 'r1bq1rk1/1pp1bppp/2np1n2/4p3/3PP3/pPP2N2/P2NBPPP/R1BQ1RK1 b - - 1 11', 'exd4'), ('Bc5', 'r2q1rk1/1pp1bppp/2n2n2/4p3/4P1b1/pPP2N2/P1QNBPPP/R1B2RK1 b - - 1 13', 'Nh5'), ('Nc4', 'r2q1rk1/1pp2ppp/2n2n2/2b1p3/4P1b1/pPP2N2/P1QNBPPP/R1B2RK1 w - - 2 14', 'b4'), ('Qe7', 'r2q1rk1/1pp2ppp/2n2n2/2b1p3/2N1P1b1/pPP2N2/P1Q1BPPP/R1B2RK1 b - - 3 14', 'b5'), ('Be3', 'r4rk1/1pp1qppp/2n2n2/2b1p3/2N1P1b1/pPP2N2/P1Q1BPPP/R1B2RK1 w - - 4 15', 'b4'), ('b5', 'r2r2k1/1pp2ppp/2n2n2/2q1p3/2N1P1b1/pPP2N2/P1Q1BPPP/3R1RK1 b - - 1 17', 'Bxf3'), ('Ne3', 'r2r2k1/2p2ppp/2n2n2/1pq1p3/2N1P1b1/pPP2N2/P1Q1BPPP/3R1RK1 w - - 0 18', 'b4'), ('Nxg4', 'r2r2k1/2p2pp1/2n2n2/1pq1p2p/4P1b1/pPP1NN2/P1Q1BPPP/3R1RK1 w - - 0 19', 'b4'), ('Nxg4', 'r2r2k1/2p2pp1/2n2n2/1pq1p2p/4P1N1/pPP2N2/P1Q1BPPP/3R1RK1 b - - 0 19', 'hxg4'), ('b4', 'r2r2k1/2p2pp1/2n5/1pq1p2p/4P1n1/pPP2N2/P1Q1BPPP/3R1RK1 w - - 0 20', 'Rc1'), ('Nc6', '3r2k1/2p2pp1/8/1pq1p2p/1n2P1n1/pQP2N2/P3BPPP/5RK1 b - - 1 22', 'Nd3'), ('Qxb5', '3r2k1/2p2pp1/2n5/1pq1p2p/4P1n1/pQP2N2/P3BPPP/5RK1 w - - 2 23', 'h3'), ('Qb2', '3r2k1/2p2pp1/8/4p2p/2BqP1n1/pQ6/P4PPP/5RK1 b - - 1 26', 'Nh6'), ('Qg3', '3r2k1/2p2pp1/8/4p2p/2B1P1n1/pQ6/Pq3PPP/5RK1 w - - 2 27', 'Bxf7+'), ('Bb3', '6k1/2p2pp1/8/4p2p/2BrP1n1/p5Q1/Pq3PPP/5RK1 w - - 4 28', 'Qb3'), ('Rxe4', '6k1/2p2pp1/8/4p2p/3rP1n1/pB4Q1/Pq3PPP/5RK1 b - - 5 28', 'c5'), ('f3', '6k1/2p2pp1/8/4p2p/4r1n1/pB4Q1/Pq3PPP/5RK1 w - - 0 29', 'h3'), ('Ne3', '6k1/2p2pp1/8/4p2p/3qr1n1/pB3PQ1/P5PP/5R1K b - - 2 30', 'Nf2+'), ('Qxd5', '2r1r1kb/3bpp2/p2p2pB/q2P4/1p4P1/3BQP2/PPP5/1K1R3R b - - 4 20', 'Rc5'), ('Bf8', '2r1r1kb/3bpp2/p2p2pB/3q4/1p4P1/3BQP2/PPP5/1K1R3R w - - 0 21', 'Bxg6'), ('Qh6', '2r1rBkb/3bpp2/p2p2p1/4q3/1p4P1/3BQP2/PPP5/1K1R3R w - - 2 22', 'Qxe5'), ('g3', 'r4rk1/pbq2pp1/1pn1p2p/2p5/3PB1n1/1PP2N2/P2N1PPP/1R1QR1K1 w - - 1 16', 'dxc5'), ('Ne7', 'r4rk1/pbq2pp1/1pn1p2p/2p5/3PB1n1/1PP2NP1/P2N1P1P/1R1QR1K1 b - - 0 16', 'Rfd8'), ('Ng5', 'r4rk1/pbq1npp1/1p2p2p/2p5/3PB1n1/1PP2NP1/P2N1P1P/1R1QR1K1 w - - 1 17', 'Bxb7'), ('Bxb7', 'r4rk1/pbq1npp1/1p2p2p/2p3N1/3PB3/1PP3P1/P2N1n1P/1R1QR1K1 w - - 0 18', 'Kxf2'), ('Bxc5', 'r1bq1rk1/pp1n1ppp/4pn2/2Pp2B1/1bP5/2N1PN2/PPQ2PPP/R3KB1R b KQ - 0 8', 'Qa5'), ('f6', 'r1b1k1nr/pp1p1ppp/2q1p3/8/1b1BP3/2N5/PPP2PPP/R2QKB1R b KQkq - 3 8', 'Qxe4+'), ('Qxg2', 'r1b1k1nr/pp1p2pp/4pp2/8/4q3/2B5/PPPQBPPP/R3K2R b KQkq - 1 11', 'Ne7'), ('h5', 'r1b1k1nr/1p1p3p/p1q2pp1/4p3/7P/2B5/PPPQBP2/1K1R2R1 w kq - 0 16', 'f4'), ('Qf6', 'r5r1/1p1k3q/p1nBb3/3pPpQB/8/8/PPP5/1K1R2R1 w - - 2 25', 'Bg6'), ('Rxg1', 'r5r1/1p1k3q/p1nBbQ2/3pPp1B/8/8/PPP5/1K1R2R1 b - - 3 25', 'Qxh5'), ('Qe7+', 'r7/1p1k4/p1nBbQ2/3pPp1q/8/8/PPP5/1K4R1 w - - 0 27', 'Rg7+'), ('b5', '2kr3r/pp1n1ppp/2p2n2/4p3/Nb2P3/4BP2/PPP1K1PP/R3N2R b - - 3 12', 'Kb8'), ('Nxc5', '2kr3r/p4ppp/2p2n2/bpn1p3/4P3/3NBP2/PPP1K1PP/R6R w - - 0 15', 'Bxc5'), ('Rhd1', '3r3r/p1k2ppp/2p2n2/bpN1p3/4P3/4BP2/PPP1K1PP/R6R w - - 1 16', 'Nd3'), ('Bb6', '1k1b4/p4ppp/2p2n2/1pN1p3/P3P1P1/4BP2/1PP1K2P/8 b - - 0 22', 'h6'), ('h6', 'r1bqr1k1/pp3ppp/5n2/3p2B1/1b1P4/2N5/PP2BPPP/R2Q1RK1 b - - 2 12', 'Bxc3'), ('Bh4', 'r1bqr1k1/pp3pp1/5n1p/3p2B1/1b1P4/2N5/PP2BPPP/R2Q1RK1 w - - 0 13', 'Bxf6'), ('Qd6', 'r1bqr1k1/pp3pp1/5n1p/3p4/1b1P3B/2N5/PP2BPPP/R2Q1RK1 b - - 1 13', 'Bxc3'), ('a4', 'r1b1r1k1/pp3pp1/1q3n1p/1N1p4/1b1P3B/8/PP2BPPP/R2Q1RK1 w - - 4 15', 'Bxf6'), ('Nc3', 'r1b1r1k1/1p3pp1/pq3n1p/1N1p4/Pb1P3B/8/1P2BPPP/R2Q1RK1 w - - 0 16', 'Bxf6'), ('Bf5', 'r1b1r1k1/1p3pp1/pq3n1p/3p4/P2P3B/2P5/4BPPP/R2Q1RK1 b - - 0 17', 'Ne4'), ('Qf5', '2r3k1/1p3pp1/p1q4p/3p4/P2P4/2PQ4/5PPP/4R1K1 w - - 1 23', 'a5'), ('Re8', '2r3k1/1p3pp1/p6p/3p1Q2/P2P4/2q5/5PPP/3R2K1 b - - 1 24', 'b5'), ('g3', '4r1k1/1p3pp1/p6p/3p1Q2/P2P4/2q5/5PPP/3R2K1 w - - 2 25', 'h3'), ('a4', 'r3kbnr/pp1b1ppp/1qn1p3/2ppP3/3P4/2PB1N2/PP3PPP/RNBQ1RK1 w kq - 1 8', 'dxc5'), ('Rc8', 'r3kbnr/pp1b1ppp/1q2p3/n2pP3/P1pP4/2P2N2/1PBN1PPP/R1BQ1RK1 b kq - 3 10', 'h6'), ('Bd3', 'rn1qkb1r/pp2pppp/5n2/2pp4/3P1Pb1/4PN2/PPP3PP/RNBQKB1R w KQkq - 2 5', 'dxc5'), ('g6', 'rn1qkb1r/pp2pppp/5n2/2pp4/3P1Pb1/3BPN2/PPP3PP/RNBQK2R b KQkq - 3 5', 'Nc6'), ('Nc6', 'r2q1rk1/3nppbp/p4np1/1p1pN3/P1pP1P2/2P1P3/1P1NQ1PP/R1B2RK1 w - - 0 13', 'e4'), ('d5', '6k1/2qn1pb1/4p1p1/1p5p/1NpPQP2/2P5/1P4PP/r1B2RK1 w - - 1 21', 'h3'), ('Qc5+', '6k1/2q2pb1/4pnp1/1p1P3p/1Np2P2/2P2Q2/1P4PP/r1B2RK1 b - - 2 22', 'Nxd5'), ('Bd4', '6k1/5pb1/4q1p1/1p5p/2p2Pn1/2P1BQ2/1PN3PP/5K2 w - - 2 27', 'Bg1'), ('Rad8', 'r5k1/p2r1ppp/Ppp1p3/4b3/4P2P/2P1BP2/1P2K1P1/R2R4 b - - 1 21', 'Rdd8'), ('Bd5', 'r1bq1rk1/2p1bppp/p1np1n2/1p2p3/3PP3/1B3N2/PPP2PPP/RNBQR1K1 w - - 0 9', 'c3'), ('Bf4', 'r4rk1/2pq1ppp/p2p1b2/1p1P1b2/8/2N5/PPP2PPP/R1BQR1K1 w - - 5 15', 'Ne2'), ('Rxe1+', 'r3r1k1/2pq1ppp/p2p1b2/1p1P1b2/5B2/2N5/PPPQ1PPP/R3R1K1 b - - 8 16', 'b4'), ('a4', '4q1k1/2p2pp1/p2p1b1p/1p1P1b2/5B2/2N4P/PPPQ1PP1/6K1 w - - 0 20', 'a3'), ('Qe4', '4q1k1/2p2pp1/3p1b1p/p2P1b2/Pp3B2/2P4P/NP1Q1PP1/6K1 b - - 0 22', 'Qxa4'), ('Bxb2', '6k1/2p2pp1/3p1b1p/3P1b2/PQ3B2/7P/1P3PP1/1qN3K1 b - - 0 25', 'Qxb2'), ('Be5', '8/2Q2ppk/3p3p/3P1b2/P4B2/7P/1b3PP1/1qN3K1 b - - 0 27', 'Qe4'), ('e4', '8/2Q2ppk/7p/3Ppb2/P7/7P/5PPK/1qN5 b - - 1 29', 'Qe4'), ('g3', '8/5Qpk/3P3p/4qb2/P3p3/7P/5PPK/2N5 w - - 1 32', 'Kh1'), ('fxe3', '8/5Qpk/3P3p/4qb2/P7/4p1PP/5P1K/2N5 w - - 0 33', 'Qe7'), ('Bf7', '8/3q2pk/3P2bp/3Q4/4PK1P/6P1/8/8 b - - 0 40', 'Qa7'), ('Bf5', 'r1b1kb1r/pp2pppp/1qn2n2/3p4/2pP1B2/2P1P3/PPQN1PPP/R3KBNR b KQkq - 1 7', 'Nh5'), ('a6', 'r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQ1RK1 b kq - 5 4', 'Nxe4'), ('Ba4', 'r1bqkb1r/1ppp1ppp/p1n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 0 5', 'Bxc6'), ('d5', 'r1bq1rk1/2ppbppp/p1n2n2/1p2p3/3PP3/1B3N2/PPP2PPP/RNBQR1K1 b - - 0 8', 'Nxd4'), ('b5', 'r1b1kb1r/1pqnppp1/p2p1n1p/8/3NPP1B/2N5/PPPQ2PP/R3KB1R b KQkq - 1 9', 'e6'), ('O-O-O', 'r1b1kb1r/2qnppp1/p2p1n1p/1p6/3NPP1B/2N5/PPPQ2PP/R3KB1R w KQkq - 0 10', 'f5'), ('b4', 'r1b1kb1r/2qnppp1/p2p1n1p/1p6/3NPP1B/2N5/PPPQ2PP/2KR1B1R b kq - 1 10', 'e6'), ('Na4', 'r1b1kb1r/2qnppp1/p2p1n1p/8/1p1NPP1B/2N5/PPPQ2PP/2KR1B1R w kq - 0 11', 'Nd5'), ('Nec5', 'r1b1kb1r/2qnppp1/p2p3p/8/Np1NnP1B/4Q3/PPP3PP/2KR1B1R b kq - 1 12', 'd5'), ('Nf5', 'r1b1kb1r/2qnppp1/p2p3p/2n5/Np1N1P1B/4Q3/PPP3PP/2KR1B1R w kq - 2 13', 'Bc4'), ('Rhe1', 'r3kb1r/1bq2pp1/p2pp2p/2n2N2/1pB2P1B/4Q3/PPP3PP/2KR3R w kq - 2 16', 'Ng3'), ('d5', 'r3kb1r/1bq2pp1/p2pp2p/2n2N2/1pB2P1B/4Q3/PPP3PP/2KRR3 b kq - 3 16', 'Ne4'), ('Bb3', 'r3kb1r/1bq2pp1/p3p2p/2np1N2/1pB2P1B/4Q3/PPP3PP/2KRR3 w kq - 0 17', 'Bxd5'), ('Qa5', '2r1kb1r/1bq2pp1/p3p2p/3p1N2/1p3P1B/1P2Q3/1PPR2PP/2K1R3 b k - 2 19', 'Kd7'), ('g6', '2r1kb1r/1b3pp1/p3p2p/q2p1N2/1p3P1B/1P2Q3/1PPR2PP/1K2R3 b k - 4 20', 'Kd7'), ('Bf6', '2r1kbr1/1b3p2/pq2p1pp/3pQ3/1p1N1P1B/1P6/1PPR2PP/1K2R3 w - - 4 23', 'Qf6'), ('Bxf4', '2r1k1r1/1b3p2/pq1bpBpp/3p4/1p1N1P2/1P6/1PPRQ1PP/1K2R3 b - - 7 24', 'Kd7'), ('g3', '2r3r1/1b1k1p2/pq2pBpp/3p4/1p1N1b2/1P1R4/1PP1Q1PP/1K2R3 w - - 2 26', 'Qf2'), ('Bg5', '2r3r1/1b1k1p2/pq2pBpp/3p4/1p1N1b2/1P1R2P1/1PP1Q2P/1K2R3 b - - 0 26', 'Bd6'), ('Rf1', '2r3r1/1b1k1p2/pq2pBpp/3p2b1/1p1N4/1P1R2P1/1PP1Q2P/1K2R3 w - - 1 27', 'Rf3'), ('Bxf6', '2r3r1/1b1k1p2/pq2pBpp/3p2b1/1p1N4/1P1R2P1/1PP1Q2P/1K3R2 b - - 2 27', 'Rcf8'), ('Qd2', '2r2r2/1b1k1p2/pq2pRpp/3p4/1p1N4/1P1R2P1/1PP1Q2P/1K6 w - - 1 29', 'Qf3'), ('h5', '2r2r2/1b1k1p2/pq2pRpp/3p4/1p1N4/1P1R2P1/1PPQ3P/1K6 b - - 2 29', 'Rce8'), ('Nf3', '2r2r2/1b1k1p2/pq2pRp1/3p3p/1p1N4/1P1R2P1/1PPQ3P/1K6 w - - 0 30', 'Qf4'), ('a5', '2r2r2/1b1k1p2/pq2pRp1/3p3p/1p6/1P1R1NP1/1PPQ3P/1K6 b - - 1 30', 'Rc7'), ('Rf1', '2r2r2/1b2kp2/1q2pRp1/p2pN2p/1p6/1P1R2P1/1PPQ3P/1K6 w - - 2 32', 'Rdf3'), ('Qg5+', '2r2r2/1b2kp2/1q2p1p1/3pN2p/pp6/1P1R2P1/1PPQ3P/1K3R2 w - - 0 33', 'Rf2'), ('Kd6', '2r2r2/1b2kp2/1q2p1p1/3pN1Qp/pp6/1P1R2P1/1PP4P/1K3R2 b - - 1 33', 'Ke8'), ('Qd8+', '4kN2/1br2p2/4pQ2/2qp3p/1p6/1p3RP1/1PP2R1P/1K6 w - - 0 40', 'Nxe6'), ('Kb1', 'rnb1k2r/p3pp1p/2pp1npQ/qp6/3PP3/2N5/PPP2PPP/2KR1BNR w kq - 1 9', 'e5'), ('Be6', 'rnb1k2r/p3pp1p/2pp1npQ/qp6/3PP3/2N5/PPP2PPP/1K1R1BNR b kq - 2 9', 'b4'), ('b4', 'rn2k2r/p3pp1p/2ppbnpQ/qp1P4/4P3/2N5/PPP2PPP/1K1R1BNR b kq - 0 10', 'Bd7'), ('Qg7', 'rn2k2r/p3pp1p/2ppPnpQ/q7/4P3/2p5/PPP2PPP/1K1R1BNR w kq - 0 12', 'exf7+'), ('d5', 'rn2kr2/p3ppQp/2ppPnp1/q7/2B1P3/2p5/PPP2PPP/1K1R2NR b q - 3 13', 'fxe6'), ('Bb3', 'rn2kr2/p3ppQp/4Pnp1/q2p4/2B5/2p5/PPP2PPP/1K1R2NR w q - 0 15', 'Rxd5'), ('Rc8', 'r3kr2/p3p1Qp/4pnp1/q2p2N1/8/1Pp5/1PP2PPP/1K1RR3 b q - 0 19', 'cxb2'), ('Nxe6', '2r1kr2/p3p1Qp/4pnp1/q2p2N1/8/1Pp5/1PP2PPP/1K1RR3 w - - 1 20', 'Rxe6'), ('b4', '2rq1r2/4bppk/p2p1n1p/1p2p2b/4P3/1PNNBP2/1PPQ2PP/3R1RK1 b - - 0 19', 'd5'), ('dxe5', 'r1bq1r2/ppp2pkp/2np1np1/4p3/3PP3/2N2N1P/PPPQ1PP1/R3KB1R w KQ - 0 11', 'O-O-O'), ('Qe7', 'r1bq1r2/ppp2pkp/2n2np1/4p3/4P3/2N2N1P/PPPQ1PP1/2KR1B1R b - - 1 12', 'Qxd2+'), ('Qg5', 'r1b2r2/ppp1qpkp/2n2np1/4p3/4P3/2N2N1P/PPPQ1PP1/2KR1B1R w - - 2 13', 'Qe3'), ('Be6', 'r1b2r2/ppp1qpkp/2n2np1/4p1Q1/4P3/2N2N1P/PPP2PP1/2KR1B1R b - - 3 13', 'a6'), ('Qg3', 'r4r2/ppp1qpk1/2n1bnpp/1B2p1Q1/4P3/2N2N1P/PPP2PP1/2KR3R w - - 0 15', 'Qe3'), ('Rad8', 'r4r2/ppp1q1k1/2n2ppp/1B1Rp2n/4P3/5N1P/PPP2PPQ/2K4R b - - 0 18', 'Nf4'), ('Rd6', '3r1r2/ppp1q1k1/2n2ppp/1B1Rp2n/4P3/5N1P/PPP2PPQ/2KR4 b - - 2 19', 'Rxd5'), ('Nh4', '5r2/pp2q1k1/2np1ppp/1B2p2n/4P3/5N1P/PPP2PPQ/2KR4 w - - 0 21', 'Qh1'), ('Nf4', '5r2/pp2q1k1/2np1ppp/1B2p2n/4P2N/7P/PPP2PPQ/2KR4 b - - 1 21', 'f5'), ('Qg4', '5r2/pp2q2k/2np1ppp/1B2p3/4Pn1N/6QP/PPP2PP1/2KR4 w - - 4 23', 'Qe3'), ('a6', '5r2/pp2q2k/2np1ppp/1B2p3/4PnQN/7P/PPP2PP1/2KR4 b - - 5 23', 'Nd4'), ('Rh1', '5r2/4q3/p1pp1p1k/4pQ1p/4P3/6Pn/PPP2P2/2KR4 w - - 2 29', 'Qxh3'), ('Rg8', '5r2/4q3/p1pp1p1k/5Qnp/4PP2/8/PPP5/2K4R b - - 0 31', 'Qe8'), ('fxg5+', '6r1/4q3/p1pp1p1k/5Qnp/4PP2/8/PPP5/2K4R w - - 1 32', 'Kb1'), ('Rxg5', '6r1/4q3/p1pp1p1k/5QPp/4P3/8/PPP5/2K4R b - - 0 32', 'fxg5')]
    # print(mistakes)
    mistakePositions = [ m[1] for m in mistakes ]
    maiaM = maiaMoves(mistakePositions, maiaFolder)
    for m in mistakes:
        print(f'Position: {m[1]}')
        print(f'Game move: {m[0]}')
        print(f'Best move: {m[2]}')
        print(maiaM[m[1]])
