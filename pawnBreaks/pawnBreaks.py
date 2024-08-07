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
    pawnBreaks = list()
    for pgnPath in pgns:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()

                for move in game.mainline_moves():
                    pawns = board.pieces(chess.PAWN, board.turn)
                    if (startSquare := move.from_square) in pawns:
                        if blockedPawns := getBlockedPawns(board):
                            endSquare = move.to_square
                            if (startSquare % 8) == (endSquare % 8):
                                if board.turn:
                                    bP = blockedPawns[False]
                                    if (endSquare % 8 != 0 and endSquare+7 in bP) or (endSquare % 8 != 7 and endSquare+9 in bP):
                                        pawnBreaks.append((board.fen(), move.uci()))
                                else:
                                    bP = blockedPawns[True]
                                    if (endSquare % 8 != 7 and endSquare-7 in bP) or (endSquare % 8 != 0 and endSquare-9 in bP):
                                        pawnBreaks.append((board.fen(), move.uci()))
                    board.push(move)
    return pawnBreaks


if __name__ == '__main__':
    print(findPawnBreaks(['../resources/Norway2024.pgn']))
