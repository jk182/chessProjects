import chess


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


if __name__ == '__main__':
    fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    print(calculatePieceActivity(fen))
