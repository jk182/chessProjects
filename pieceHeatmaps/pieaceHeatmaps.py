import chess
from chess import pgn
import matplotlib.pyplot as plt
import numpy as np


def getPieceData(pgnPath: str, pieceType: int, color: bool, minMove: int = 0, maxMove: int = 200) -> list:
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

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            board = game.board()
            gameMoves = 0
            for move in game.mainline_moves():
                board.push(move)
                if not board.turn == color:
                    if gameMoves >= minMove:
                        for square in board.pieces(pieceType, color):
                            squares[square] += 1
                    totalMoves += 1
                    gameMoves += 1
                    if gameMoves >= maxMove:
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


def plotPieceHeatmaps(pgnPath: str, color: bool, minMove: int = 0, maxMove: int = 200):
    fig, ((pawn, knight), (bishop, rook), (queen, king)) = plt.subplots(3, 2, figsize=(6, 8))
    ax = [pawn, knight, bishop, rook, queen, king]
    files = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    ranks = [8, 7, 6, 5, 4, 3, 2, 1]
    pieceNames = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']
    for p in range(chess.PAWN, chess.KING+1):
        data = getPieceData(pgnPath, p, color, minMove, maxMove)
        # Mapping the chessboard to the output
        data = np.reshape(list(reversed(data)), (8, 8))
        data = [list(reversed(l)) for l in data]
        ax[p-1].imshow(data, cmap='plasma')
        ax[p-1].set_title(pieceNames[p-1])

        ax[p-1].set_xticks(np.arange(8), labels=files)
        ax[p-1].set_yticks(np.arange(8), labels=ranks)
        ax[p-1].set_xticks(np.arange(9)-.5, minor=True)
        ax[p-1].set_yticks(np.arange(9)-.5, minor=True)
        ax[p-1].grid(which='minor', color="black", linestyle='-', linewidth=1)

        # annotating the heatmap (it looks horrible for now)
        """
        for i in range(8):
            for j in range(8):
                text = ax[p-1].text(j, i, round(data[i][j], 2), ha="center", va="center", color="w")
        """
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    pgn = '../resources/carlsbad.pgn'
    plotPieceHeatmaps(pgn, chess.WHITE, minMove=5)
