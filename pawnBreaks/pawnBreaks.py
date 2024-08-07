import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chess import engine, pgn, Board
import chess


def getBlockedPawns(board: Board) -> dict:
    """
    This function finds all the blocked pawns in a position.
    board: Board
        The position as a chess.Board
    return -> dict
        Dictionary with the colors as keys and a list of the squares of the blocked pawns as values
    """
    blockedPawns = dict()
    wPawns = board.pieces(chess.PAWN, chess.WHITE)
    bPawns = board.pieces(chess.PAWN, chess.BLACK)
    for square in wPawns:
        if square+8 in bPawns:
            if blockedPawns:
                blockedPawns[chess.WHITE].append(square)
                blockedPawns[chess.BLACK].append(square+8)
            else:
                blockedPawns[chess.WHITE] = [square]
                blockedPawns[chess.BLACK] = [square+8]
    return blockedPawns


def findPawnBreaks(pgns: list):
    for pgnPath in pgns:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()

                for move in game.mainline_moves():
                    wPawns = board.pieces(chess.PAWN, chess.WHITE)
                    bPawns = board.pieces(chess.PAWN, chess.BLACK)
                    if (square := move.from_square) in wPawns:
                        print(move)


if __name__ == '__main__':
    findPawnBreaks(['../resources/Svidler-Malaniuk,1998.pgn'])
