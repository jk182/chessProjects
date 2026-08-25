import chess
import chess.pgn
import polars as pl

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def getEndgameType(board: chess.Board) -> str:
    """
    This function gets the type of endgame on the board
    Return categories:
    """
    fen = board.fen()
    whitePieces = list()
    blackPieces = list()
    for s in fen.split()[0]:
        if s in 'NBRQ':
            whitePieces.append(s)
        elif s in 'nbrq':
            blackPieces.append(s)
        
    return f'{"".join(sorted(whitePieces))}-{"".join(sorted(blackPieces))}'


def extractEndgameConversionRates(pgnPaths: list) -> pl.DataFrame:
    data = dict()
    keys = ['WhiteElo', 'BlackElo', 'EndgameType', 'Result', 'StartEval', 'EndEval', 'Flawless']

    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                wElo = game.headers["WhiteElo"]
                bElo = game.headers["BlackElo"]
                result = game.headers["Result"]

                node = game
                lastEndgameType = None
                flawless = True
                plySinceEndgameType = 0

                while not node.is_end():
                    node = node.variations[0]
                    board = node.board()

                    if functions.getGamePhase(board) == 'endgame':
                        endgameType = getEndgameType(board)
                        if lastEndgameType is None:
                            lastEndgameType = endgameType
                            if node.eval() is not None:
                                startEval = node.eval().white().score(mate_score=10000)
                            else:
                                startEval = None
                        if endgameType == lastEndgameType:
                            plySinceEndgameType += 1
                            # TODO: check if the advantage/equality was thrown away at some point
                        else:
                            if plySinceEndgameType >= 5:
                                data['WhiteElo'].append(wElo)
                                data['BlackElo'].append(bElo)
                                data['EndgameType'].append(lastEndgameType)
                                data['Result'].append(result)
                                data['StartEval'].append(startEval)
                                if node.eval() is not None:
                                    data['EndEval'].append(node.eval().white().score(mate_score=10000))
                                else:
                                    data['EndEval'].append(None)
                                data['Flawless'].append(flawless)

                            lastEndgameType = endgameType
                            plySinceEndgameType = 0
                            flawless = True

                if plySinceEndgameType >= 5:
                    data['WhiteElo'].append(wElo)
                    data['BlackElo'].append(bElo)
                    data['EndgameType'].append(endgameType)
                    data['Result'].append(result)
                    data['StartEval'].append(startEval)
                    data['EndEval'].append(None)
                    data['Flawless'].append(flawless)

    df = pl.DataFrame(data)
    return df


if __name__ == '__main__':
    pgnFolder = '../out/lichessDB/'
    pgnPaths = [f'{pgnFolder}{p}' for p in os.listdir(pgnFolder) if 'endgame' in p]
    print(extractEndgameConversionRates([pgnPaths[6]]))
