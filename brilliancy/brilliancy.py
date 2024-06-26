from engineCommands import *
import chess
from chess import pgn
import re
import time
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def analyse(gamesFile: str, outfile: str, engine: engine, nodes: int) -> list:
    """
    This function plays thorugh the games in a file, analyses them and returns a 
    list of the evaluations and WDL after every move
    gamesFile: str
        The name of a PGN file containing the games to analyse
    outfile: str
        The path of the output PGN file with the WDL comments
    engine: engine
        The engine used for the analysis
    nodes: int
        The number of nodes searched for every move
    return -> list
        A list of lists for each game, containing the WDL and score after every move
    """
    
    brC = 0
    sftime = 8
    s = ''
    gameNR = 1
    with open(gamesFile, 'r') as pgn:
        sf = configureEngine('stockfish', {'Threads': '4'})
        while (game := chess.pgn.read_game(pgn)):
            # print(f'Starting with game {gameNR}...')
            gameNR += 1
            
            print(game.headers["White"])
            print(game.headers["Black"])
            board = game.board()
            phead = list()
            for move in game.mainline_moves():
                # print(move)

                # .analysis instead of .analyse!
                info = leela.analysis(board, chess.engine.Limit(nodes=nodes))
                for i in info:
                    for j in i.values():
                        p = re.findall('P: *\d*\.\d\d%', str(j))
                        if move.uci() in str(j) and p:
                            phead.append(float(p[0].split(' ')[-1][:-1]))
                            # first test value 2
                            if phead[-1] < 2.5:
                                # Stockfish analysis to prove that a move is actually good
                                bestMove = sf.analyse(board, chess.engine.Limit(time=sftime))['pv'][0]
                                if bestMove == move:
                                    print('\033[92mBrilliancy!!\033[0m')
                                    brC += 1
                                    print(board)
                                    print(move)
                                    print(p)
                            elif phead[-1] < 2.5:
                                print(board)
                                print(move)
                                print(p)
                board.push(move)
            # print(phead)

    # print(s, file=open(outfile, 'w'))
    engine.quit()
    sf.quit()
    print(sum(phead)/len(phead))
    print(f'Number of brilliancies: {brC}')
    return [phead]


def surprise(gamesFile: str, engine: engine) -> dict:
    """
    This method takes a PGN file and gives to P values for each move indexed by the players
    """

    moves = [0,0]
    m = 0
    surp = dict()
    cache = dict()
    with open(gamesFile, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            wMove = True
            white = game.headers["White"]
            black = game.headers["Black"]
            for player in [white, black]:
                if player not in surp.keys():
                    surp[player] = list()
            board = game.board()
            for k, move in enumerate(game.mainline_moves()):
                m += 1
                # print(move)
                broken = False

                # Without the cache, there are still around 50 positions missing
                if k < 10:
                    fen = board.fen()
                    if fen not in cache.keys():
                        info = leela.analysis(board, chess.engine.Limit(nodes=1))
                        cache[fen] = [ i for i in info ]
                        print(cache)
                    else:
                        # for some reason, lines from the info get deleted AFTER they have been saved in the cache 
                        # print('WTF is going on?!')
                        # print(len([i for i in cache.values()]))

                        # copying the data doesn't help
                        info = cache[fen].copy()
                else:
                    # .analysis instead of .analyse!
                    info = leela.analysis(board, chess.engine.Limit(nodes=1))
                for i in info:
                    if 'string' in i.keys():
                        js = i['string']
                        if move.uci() in js:
                            p = re.findall('P: *\d*\.\d*%', js)
                            phead = float(p[0].split(' ')[-1][:-1])
                            if wMove:
                                player = white
                                moves[0] += 1
                            else:
                                player = black
                                moves[1] += 1
                            surp[player].append(phead)
                            broken = True
                    if broken:
                        break

                board.push(move)
                wMove = not wMove

    # print(s, file=open(outfile, 'w'))
    engine.quit()
    for k,v in surp.items():
        print(f'{k}:\t{sum(v)/len(v)} {max(v)} {min(v)}')
        print(len(v))
    print(moves)
    print(m)
    return surp


def compareNets(networks, pgn):
    for i, network in enumerate(networks):
        print(f'Network {i+1}: {network}')
        leela = configureEngine('lc0', {'WeightsFile': network, 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})
        analyse(pgn, '', leela, 1)

    leela.quit()


def analysePositions(fens:dict, lc0:engine, sf: engine):
    '''
    fens:
        A dictionary containing the FENs of the positions and the move played in the game
    lc0:
        Leela
    '''

    sftime = 2
    wpCutoff = 15
    phead = list()
    for fen, move in fens.items():
        board = chess.Board(fen)
        info = lc0.analysis(board, chess.engine.Limit(nodes=1))
        for i in info:
            for j in i.values():
                p = re.findall('P: *\d*\.\d\d%', str(j))
                if move in str(j) and p:
                    phead.append(float(p[0].split(' ')[-1][:-1]))
                    # Stockfish analysis to prove that a move is actually good
                    if phead[-1] < 2.5:
                        analysis = sf.analyse(board, chess.engine.Limit(time=sftime), multipv=2)
                        bestMove = analysis[0]['pv'][0]
                        if bestMove.uci() == move:
                            s1 = analysis[0]['score'].pov(board.turn)
                            s2 = analysis[1]['score'].pov(board.turn)
                            print(s1, s2)
                            if s1.is_mate() and s2.is_mate():
                                if s1.mate() * s2.mate() > 0:
                                    continue
                            elif not (s1.is_mate() or s2.is_mate()):
                                wp1 = functions.winP(s1.score())
                                wp2 = functions.winP(s2.score())
                                if wp1-wp2 < wpCutoff:
                                    continue
                            elif s1.is_mate() and not s2.is_mate():
                                if s1.mate()*s2.score() > 0 and abs(s2.score()) > 500:
                                    continue
                            print('\033[92mBrilliancy!!\033[0m')
                    print(board)
                    print(move)
                    print(p)


def isBrilliancy(fen: str, move: str, lc0: engine, sf: engine) -> bool:
    """
    This function evaluates if a move in a given position is a brilliancy or not
    fen: str
        The FEN string of the position
    move: str
        The move played in the position
    lc0: engine
        A configured LC0 engine
    sf: engine
        A configured Stockfish engine
    return -> bool
        If the move was a brilliancy or not
    """

    sftime = 4
    wpCutoff = 15
    brilliancyCutoff = 2.5
    phead = list()
    board = chess.Board(fen)
    info = lc0.analysis(board, chess.engine.Limit(nodes=1))
    for i in info:
        for j in i.values():
            p = re.findall('P: *\d*\.\d\d%', str(j))
            if move in str(j) and p:
                phead = float(p[0].split(' ')[-1][:-1])
                print(phead)
                if phead < brilliancyCutoff:
                    analysis = sf.analyse(board, chess.engine.Limit(time=sftime), multipv=2)
                    bestMove = analysis[0]['pv'][0]
                    if bestMove.uci() == move:
                        if len(analysis) == 1:
                            print(board, move)
                            return False
                        s1 = analysis[0]['score'].pov(board.turn)
                        s2 = analysis[1]['score'].pov(board.turn)
                        print(s1, s2)
                        if s1.is_mate() and s2.is_mate():
                            if s1.mate() * s2.mate() > 0:
                                return False
                        elif not (s1.is_mate() or s2.is_mate()):
                            wp1 = functions.winP(s1.score())
                            wp2 = functions.winP(s2.score())
                            if wp1-wp2 < wpCutoff:
                                return False
                        elif s1.is_mate() and not s2.is_mate():
                            if s1.mate() <= 5 and abs(s2.score()) < 1000:      # Unsure if quick mates should be called brilliant
                                return True
                            if s1.mate()*s2.score() > 0 and abs(s2.score()) > 500:
                                return False
                        return True
    return False


def findBrilliancies(pgnPath: str, lc0: engine, sf: engine, outPath: str) -> list():
    """
    This functions finds the brilliancies in a given PGN file
    """
    brilliancies = list()
    gameNr = 0
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            gameNr += 1
            print(f'Game {gameNr}:')
            if 'Variant' in game.headers.keys():
                if game.headers['Variant'] == 'Chess960':
                    continue
            board = chess.Board()
            newGame = chess.pgn.Game()
            newGame.headers = game.headers
            node = newGame
            hasBr = False
            print(game.headers)
            for move in game.mainline_moves():
                node = node.add_variation(move)
                if isBrilliancy(board.fen(), move.uci(), lc0, sf):
                    print(board)
                    print(move.uci())
                    brilliancies.append((board.fen(), move.uci()))
                    hasBr = True
                    node.comment = "!!"
                board.push(move)
            if hasBr:
                print(newGame, file=open(outPath, 'a+'), end='\n\n')
    return brilliancies


if __name__ == '__main__':
    # leela = configureEngine('lc0', {'WeightsFile': '/Users/julian/chess/w320x24', 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})
    leela = configureEngine('lc0', {'WeightsFile': '/home/julian/Desktop/smallNet.gz', 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})
    sf = configureEngine('stockfish', {'Threads': '10'})
    networks = ['/Users/julian/chess/nets/smallNet', '/Users/julian/chess/nets/mediumNet', '/Users/julian/chess/nets/largeNet']
    positions = {'1n6/1b1n1k2/5P1p/p1p3qp/4r3/1P6/P1Q2NPP/R4RK1 b - - 0 1': 'g5g2', 'r4r1k/pp1b1p1p/1q1p4/4pP1P/3R4/1PN1Q3/1PP3P1/2K2R2 w - - 0 22': 'e3h6',
                 '4b3/1p2kp1N/pn1rp2p/q4P2/P2r4/3B4/1P2Q1PP/2R2RK1 w - - 1 25': 'b2b4',
                 '2r3r1/3q3p/p6b/Pkp1B3/1p1p1P2/1P1P1Q2/2R3PP/2R3K1 w - - 1 31': 'e5c7', 
                 'r3qr1k/pp3pbp/2pn4/7Q/3pP3/2NB3P/PPP3P1/R4RK1 w - - 0 19': 'f1f6',
                 '8/8/1p3pk1/2b2RPp/4P2K/2Q3PP/p4q2/8 b - - 1 41': 'f2f4',
                 '8/8/4kpp1/3p1b2/p6P/2B5/6P1/6K1 b - - 2 47': 'f5h3',
                 'rnbq1rk1/6pp/p1p2p2/1p1pN3/1bpPP3/1P4P1/P1Q2PBP/R1B2RK1 w - - 0 13': 'e4d5',
                 '4rrk1/1bpR1p2/1pq1pQp1/p3P2p/P1PR3P/5N2/2P2PP1/6K1 w - h6 0 31': 'g1h2',
                 'r5k1/ppp2r1p/3p3b/3Pn3/1n2PPp1/1P2K1P1/PBB1N2q/R2Q3R b - - 2 24': 'f7f4',
                 '5rk1/p1pb2pp/2p5/3p3q/2P3n1/1Q4B1/PP1NprPP/R3R1K1 b - - 0 20': 'f2g2'}
    aPos = {'r6r/qb2pk1p/p1np1ppQ/2pN4/4P3/5P2/PP4PP/2KR1B1R w - - 0 19': 'd5e7',
            '3r2k1/p2r1pp1/1pQ3p1/3P2q1/P7/6P1/5P1P/2R1R1K1 w - - 0 30': 'c6d7',
            '4n1k1/pbrq2p1/4rB1Q/4P3/4p3/6RP/PP4P1/5RK1 w - - 1 33': 'f6g7',
            '8/1p3k1r/p3pp2/2PN2p1/PP6/7P/5qRK/3Q4 b - - 2 53': 'h7h3',
            '3q1r1k/1b1nNppp/4p3/1Nnp4/1R6/4PP2/2Q1B1PP/6K1 w - - 9 27': 'c2h7',
            '8/Q5p1/8/5pk1/1P2q3/KQq5/P7/8 b - - 2 46': 'e4b4'}
    # analysePositions(positions, leela, sf)
    outPath = '../out/brillianciesAlekhine.pgn'
    for k, v in aPos.items():
        print(isBrilliancy(k, v, leela, sf))
    # findBrilliancies('../resources/alekhine2.pgn', leela, sf, outPath)
    sf.quit()
    leela.quit()
