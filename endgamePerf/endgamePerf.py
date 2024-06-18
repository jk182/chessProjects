import berserk
import chess
from chess import pgn
import time
import requests


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



if __name__ == '__main__':
    with open('../resources/tbToken', 'r') as tokenFile:
        token = tokenFile.read().strip()

    pos = '8/4k3/8/8/8/8/4P3/4K3 w - - 0 1'
    pos2 = '4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'
    # print(tablebaseLookup(token, pos)['category'])
    # print(tablebaseLookup(token, pos2))
    games = ['../out/games/norwayChessOpen2024-out.pgn', '../out/games/candidates2024-WDL+CP.pgn', '../out/games/2700games2023-out.pgn']
    g2 = ['../out/games/2700games2023-out.pgn']
    print(getEndgameMistakes(token, g2))
