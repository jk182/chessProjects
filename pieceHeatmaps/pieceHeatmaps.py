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
    minMove: int
        A lower cutoff for the move number
    maxMove: int
        An upper cutoff for the move number
    return -> list
        A list of length 64 where each entry is the percentage of the number of moves a piece spent on that square
    """
    squares = [0] * 64
    totalMoves = 0

    with open(pgnPath, 'r', encoding="latin-1") as pgn:
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


def getAllPieceData(pgnPath: str, color: bool, minMove: int = 0, maxMove: int = 200) -> list:
    """
    This function generates a list of the piece data from every piece
    pgnPath: str
        Path to the PGN file
    color: bool
        The color for the piece data
    minMove: int
        A lower cutoff for the move number
    maxMove: int
        An upper cutoff for the move number
    return -> list
        A list containing the piece data (from getPieceData) for every piece
    """
    data = list()
    for piece in range(chess.PAWN, chess.KING+1):
        data.append(getPieceData(pgnPath, piece, color, minMove, maxMove))
    return data


def plotHeatmap(pieceData: list):
    """
    This plots a heatmap of a single piece with the data from getPieceData
    """
    nData = list(reversed(pieceData))
    plt.figure(figsize=(8, 8))
    plt.imshow(np.reshape(nData, (8, 8)), cmap='plasma', interpolation='nearest')
    plt.colorbar()
    plt.show()


def plotPieceHeatmaps(pieceData: list, color: bool, filename: str = None):
    """
    This fucntion plots the heatmaps for all pieces
    pieceData: list
        Output from getAllPieceData
    color: bool
        Color one is looking at (only for the titles)
    filename: str
        The name of the file the heatmap should be saved to.
        If no name is give, the heatmap will be shown instead.
    """
    fig, ((pawn, knight), (bishop, rook), (queen, king)) = plt.subplots(3, 2, figsize=(6, 8))
    ax = [pawn, knight, bishop, rook, queen, king]
    files = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    ranks = [8, 7, 6, 5, 4, 3, 2, 1]
    pieceNames = ['Pawns', 'Knights', 'Bishops', 'Rooks', 'Queen', 'King']
    if color:
        colorName = 'White'
    else:
        colorName = 'Black'
    for p in range(chess.PAWN, chess.KING+1):
        data = pieceData[p-1]
        # Mapping the chessboard to the output
        data = np.reshape(list(reversed(data)), (8, 8))
        data = [list(reversed(l)) for l in data]
        im = ax[p-1].imshow(data, cmap='plasma')
        ax[p-1].set_title(f'{colorName} {pieceNames[p-1]}')

        ax[p-1].set_xticks(np.arange(8), labels=files)
        ax[p-1].set_yticks(np.arange(8), labels=ranks)
        ax[p-1].set_xticks(np.arange(9)-.5, minor=True)
        ax[p-1].set_yticks(np.arange(9)-.5, minor=True)
        ax[p-1].grid(which='minor', color="black", linestyle='-', linewidth=1)
        ax[p-1].figure.colorbar(im)

    fig.tight_layout()
    fig.patch.set_facecolor('#e6f7f2')
    if filename:
        plt.savefig(f'../out/{colorName}_{filename}.png', dpi=500)
    else:
        plt.show()


if __name__ == '__main__':
    pgn = '../resources/carlsbad.pgn'
    # carlsbad = getAllPieceData(pgn, chess.WHITE, minMove=7, maxMove=30)
    # plotPieceHeatmaps(carlsbad, chess.WHITE, filename='carlsbadHeatmap')
    spanish = '../resources/spanishMorphy.pgn'
    # spanishData = getAllPieceData(spanish, chess.WHITE, minMove=7, maxMove=30)
    # plotPieceHeatmaps(spanishData, chess.WHITE, filename='spanishHeatmap')
    kid = '../resources/KID.pgn'
    KIDdataW = getAllPieceData(kid, chess.WHITE, minMove=7, maxMove=30)
    KIDdataB = getAllPieceData(kid, chess.BLACK, minMove=7, maxMove=30)
    plotPieceHeatmaps(KIDdataW, chess.WHITE)
    plotPieceHeatmaps(KIDdataB, chess.BLACK)
    # wcc = '../out/games/ding-gukesh-G3.pgn'
    # wccData = getAllPieceData(wcc, chess.WHITE)
    # plotPieceHeatmaps(wccData, chess.WHITE, filename='wcc2024G3Heatmap')
