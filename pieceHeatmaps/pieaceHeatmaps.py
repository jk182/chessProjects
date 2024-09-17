import chess
from chess import pgn
import matplotlib.pyplot as plt
import numpy as np


def getPieceData(pgnPath: str, pieceType: int, color: bool, minMove: int = 0, maxMove: int = None) -> list:
    """
    This function gets the relative number of moves a piece spent on each square in the PGN
    pgnPath: str
        Path to the PGN file
    pieceType: int
        Type of the piece, 1-6 without colors
    color: bool
        The color of the piece in question
    return -> list
        A list of length 64 where each entry is the percentage of the number of moves a piece spent on that square
    """
    squares = [0] * 64
    totalMoves = 0

    if not maxMove:
        maxMove = 300

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                # This should count pieces and moves twice, which should cancel out
                totalMoves += 1
                if (totalMoves/2) >= minMove:
                    for square in board.pieces(pieceType, color):
                        squares[square] += 1
                if (totalMoves / 2) >= maxMove:
                    break

    return [s/totalMoves for s in squares]


def plotHeatmap(pieceData: list):
    """
    This plots a heatmap of a piece with the data from getPieceData
    """
    nData = list(reversed(pieceData))
    plt.figure(figsize=(8, 8))
    plt.imshow(np.reshape(nData, (8, 8)), cmap='plasma', interpolation='nearest')
    plt.colorbar()
    plt.show()


if __name__ == '__main__':
    pgn = '../resources/carlsbad.pgn'
    wKnightData = getPieceData(pgn, chess.KNIGHT, chess.WHITE, minMove=5, maxMove=20)
    wBishopData = getPieceData(pgn, chess.BISHOP, chess.WHITE)
    plotHeatmap(wKnightData)
    plotHeatmap(wBishopData)
