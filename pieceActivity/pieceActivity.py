import chess
from chess import pgn
import matplotlib.pyplot as plt


def calculatePieceActivity(fen: str) -> list:
    """
    This function calculates the activity of the pieces for a given position
    fen: str
        The FEN string of the position
    return -> tuple
        The activity scores for White and Black
    """
    activity = [0, 0]
    board = chess.Board(fen)
    for color in [chess.WHITE, chess.BLACK]:
        if color:
            index = 0
        else:
            index = 1
        for pieceType in range(2, 7):
            # starting at 2 to remove pawns from the count
            for piece in board.pieces(pieceType, color):
                for square in board.attacks(piece):
                    if board.color_at(square) != color:
                        activity[index] += 1
                        if color == chess.WHITE and square >= 32:
                            activity[index] += 1
                        elif color == chess.BLACK and square <= 31:
                            activity[index] += 1
    return activity


def plotPieceActivity(pgnPath: str, filename: str = None):
    """
    This function plots the piece activity for White and Black in a given game.
    pgnPath: str
        Path to the PGN file of the game
    filname: str
        The name of the file to which the graph will be saved.
        If no name is given, the graph will be shown instead of saved.
    """
    white = list()
    black = list()
    with open(pgnPath, 'r') as pgn:
        game = chess.pgn.read_game(pgn)
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            activity = calculatePieceActivity(board.fen())
            white.append(activity[0])
            black.append(activity[1])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(1, len(white)+1), white, color='#f8a978', label='White piece activity')
    ax.plot(range(1, len(black)+1), black, color='#111111', label='Black piece activity')

    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Move number')
    ax.set_ylabel('Piece activity')
    ax.set_xlim(1, len(white))
    ax.set_ylim(0)
    ax.set_xticks(list(range(1, len(white)))[::10])
    ax.set_xticklabels([i//2 for i in range(len(white))[::10]])
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


if __name__ == '__main__':
    fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    pgn = '../resources/steinitz-vonBardeleben.pgn'
    plotPieceActivity(pgn)
    plotPieceActivity('../resources/jinshi-ding.pgn')
