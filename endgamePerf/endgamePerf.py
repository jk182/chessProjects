# import berserk
import chess
from chess import pgn
import time
import requests
import pickle as pkl

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions import configureEngine
import plotting_helper


def tablebaseLookup(token: str, fen: str) -> dict:
    """
    This function makes a tablebase lookup for a given position
    token: str
        The Lichess token in order to use the Lichess API for the tablebase lookup
    fen: str
        The position as a FEN string
    return -> dict
        The result form the tablebase lookup
    """
    session = berserk.TokenSession(token)
    client = berserk.Client(session=session)
    tb = client.tablebase.look_up(fen)
    # tb = requests.get(f'http://tablebase.lichess.ovh/standard?fen={fen}')
    return tb


def getEndgameMistakes(token: str, pgnPaths: list) -> dict:
    """
    This function calculates the number of endgame mistakes in the PGNs given.
    toke: str
        A Lichess token to use the Lichess API for the tablebase lookup
    pgnPaths: list
        The paths of the PGN files to analyse
    return -> dict:
        Dictionary indexed by players and containing the number of mistakes, games with mistakes and total games as values
    """
    mistakes = dict()
    requests = 0
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                w = game.headers['White']
                b = game.headers['Black']

                for p in [w, b]:
                    if p not in mistakes.keys():
                        mistakes[p] = [0, 0, 0]

                board = game.board()
                lastState = None
                endgameReached = False
                m = 0

                for move in game.mainline_moves():
                    if board.turn:
                        player = w
                    else:
                        player = b
                    board.push(move)
                    if len(board.piece_map()) > 7:
                        continue

                    if not endgameReached:
                        print(w, b)
                        for p in [w, b]:
                            mistakes[p][2] += 1
                    endgameReached = True
                    time.sleep(0.4)        # To avoid too many requests
                    state = tablebaseLookup(token, board.fen())['category']
                    requests += 1
                    print(state, requests)
                    if not lastState:
                        lastState = state
                        continue
                    if lastState == 'draw' and state == 'draw':
                        continue
                    if lastState == 'draw' or state == 'draw':
                        mistakes[player][0] += 1
                        lastState = state
                        continue
                    if lastState != state:      # since the side to move changes on each turn
                        lastState = state
                        continue
                    mistakes[player][0] += 1
    return mistakes


def getEndgameType(board: chess.Board) -> str:
    """
    This returns the type of endgame on the board.
    The types are:
        pawn
        rook
        queen
    """
    pieces = set(board.piece_map().values())
    pieces.discard(chess.Piece.from_symbol('K'))
    pieces.discard(chess.Piece.from_symbol('k'))

    if len(pieces) == 0:
        return None

    pieces.discard(chess.Piece.from_symbol('P'))
    pieces.discard(chess.Piece.from_symbol('p'))

    if len(pieces) == 0:
        return 'pawn'

    if len(pieces) == 2:
        if chess.Piece.from_symbol('Q') in pieces and chess.Piece.from_symbol('q') in pieces:
            return 'queen'
        if chess.Piece.from_symbol('R') in pieces and chess.Piece.from_symbol('r') in pieces:
            return 'rook'
        if chess.Piece.from_symbol('N') in pieces and chess.Piece.from_symbol('n') in pieces:
            return 'knight'
        if chess.Piece.from_symbol('B') in pieces and chess.Piece.from_symbol('b') in pieces:
            return 'bishop'

    return None


def getEndgamePerformance(pgnPath: str, player: str, sf: chess.engine) -> dict:
    scores = dict()
    depth = 22
    timeLimit = 4
    with open(pgnPath, 'r', encoding='windows-1252') as pgn:
        while game := chess.pgn.read_game(pgn):
            if player in game.headers["White"]:
                white = True
            elif player in game.headers["Black"]:
                white = False
            else:
                continue

            if game.headers["Result"] == "1-0":
                wPoints = 1
            elif game.headers["Result"] == "1/2-1/2":
                wPoints = 0.5
            elif game.headers["Result"] == "0-1":
                wPoints = 0
            else:
                print('Result not found')
                continue

            lastEndgame = None
            startScore = None
            endgames = set()
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                endgame = getEndgameType(board)
                if endgame == lastEndgame:
                    continue

                if endgame is not None:
                    info = sf.analyse(board, chess.engine.Limit(time=timeLimit))
                    if 'wdl' not in info.keys():
                        print('WDL not found')
                        print(info)
                        continue
                    wdl = list(chess.engine.PovWdl.white(info['wdl']))
                    endgames.add(endgame)
                    if white:
                        startScore = (wdl[0] + 0.5*wdl[1])/1000
                    else:
                        startScore = (wdl[2] + 0.5*wdl[1])/1000

                if lastEndgame is not None:
                    if lastEndgame not in scores.keys():
                        scores[lastEndgame] = [0, 0, 0]
                    scores[lastEndgame][1] += startScore
                    scores[lastEndgame][2] += 1
                    if white:
                        scores[lastEndgame][0] += wPoints
                    else:
                        scores[lastEndgame][0] += 1-wPoints

                lastEndgame = endgame

            if endgame == lastEndgame and endgame is not None:
                    if lastEndgame is not None:
                        if lastEndgame not in scores.keys():
                            scores[lastEndgame] = [0, 0, 0]
                        scores[lastEndgame][1] += startScore
                        scores[lastEndgame][2] += 1
                        if white:
                            scores[lastEndgame][0] += wPoints
                        else:
                            scores[lastEndgame][0] += 1-wPoints
    return scores


def plotEndgamePerformances(players: dict, endgameTypes: list = ['pawn', 'knight', 'bishop', 'rook', 'queen']):
    """
    players: dict
        Dictionary indexed by player name and containing the path to the pickle file of the data as value
    """
    plotData = list()
    for player, path in players.items():
        with open(path, 'rb') as f:
            data = pkl.load(f)
        plotData.append([])
        for endgameType in endgameTypes:
            if endgameType not in data.keys():
                plotData[-1].append(0)
            else:
                plotData[-1].append((data[endgameType][0]-data[endgameType][1])/data[endgameType][2])

    plotting_helper.plotPlayerBarChart(plotData, list(players.keys()), 'Difference between score and expected score per game', 'Endgames', endgameTypes)


if __name__ == '__main__':
    # with open('../resources/tbToken', 'r') as tokenFile:
        # token = tokenFile.read().strip()

    pos = '8/4k3/8/8/8/8/4P3/4K3 w - - 0 1'
    pos2 = '4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'
    pos3 = '4rk2/ppp2ppp/8/3nPP2/3P4/8/P2B2PP/2R3K1 w - - 5 25'
    rook = '1rk5/1p4R1/8/1p4K1/P7/8/8/8 w - - 0 46'
    pawn = '8/8/1p6/p3kpP1/8/5K2/P1P5/8 b - - 0 39'
    # print(tablebaseLookup(token, pos)['category'])
    # print(tablebaseLookup(token, pos2))
    games = ['../out/games/norwayChessOpen2024-out.pgn', '../out/games/candidates2024-WDL+CP.pgn', '../out/games/2700games2023-out.pgn']
    g2 = ['../out/games/2700games2023-out.pgn']
    # print(getEndgameMistakes(token, g2))
    players = {'Carlsen': '../resources/carlsenEndgames.pkl', 'Nakamura': '../resources/nakaEndgames.pkl', 'Caruana': '../resources/caruanaEndgames.pkl', 'MVL': '../resources/mvlEndgames.pkl', 'Nepo': '../resources/nepoEndgames.pkl'}
    youngPlayers = {'Firouzja': '../resources/firouzjaEndgames.pkl', 'Erigaisi': '../resources/erigaisiEndgames.pkl', 'Gukesh': '../resources/gukeshEndgames.pkl', 'Abdusattorov': '../resources/abdusattorovEndgames.pkl', 'Keymer': '../resources/keymerEndgames.pkl'}
    plotEndgamePerformances(players)
    plotEndgamePerformances(youngPlayers)

    """
    sf = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192', 'UCI_ShowWDL': 'true'})
    # print(getEndgamePerformance('../resources/games/Rubinstein-Duras.pgn', 'Rubinstein', sf))
    # print(getEndgamePerformance('../resources/carlsen2019.pgn', 'Carlsen', sf))
    print('Carlsen')
    # print(getEndgamePerformance('../resources/carlsenGames.pgn', 'Carlsen', sf))
    print('Caruana')
    # print(getEndgamePerformance('../resources/caruanaGames.pgn', 'Caruana', sf))
    print('Nakamura')
    # print(getEndgamePerformance('../resources/nakaGames.pgn', 'Nakamura', sf))
    print('MVL')
    with open('../resources/mvlEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/mvlGames.pgn', 'Vachier-Lagrave', sf)
        print(p)
        pkl.dump(p, f)
    print('Nepo')
    with open('../resources/nepoEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/nepoGames.pgn', 'Nepom', sf)
        print(p)
        pkl.dump(p, f)
    with open('../resources/firouzjaEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/firouzjaGames.pgn', 'Firouzja', sf)
        print(p)
        pkl.dump(p, f)
    with open('../resources/abdusattorovEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/abdusattorovGames.pgn', 'Abdusattorov', sf)
        print(p)
        pkl.dump(p, f)
    with open('../resources/keymerEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/keymerGames.pgn', 'Keymer', sf)
        print(p)
        pkl.dump(p, f)
    with open('../resources/carlsenEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/carlsenGames.pgn', 'Carlsen', sf)
        print(p)
        pkl.dump(p, f)
    with open('../resources/caruanaEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/caruanaGames.pgn', 'Caruana', sf)
        print(p)
        pkl.dump(p, f)
    with open('../resources/nakaEndgames.pkl', 'wb+') as f:
        p = getEndgamePerformance('../resources/nakaGames.pgn', 'Nakamura', sf)
        print(p)
        pkl.dump(p, f)
    sf.quit()
    """
