import chess
import chess.pgn


def isForcingMove(board: chess.Board, move: chess.Move) -> bool:
    """
    This function determines whether the given move is a forcing move in the position
    """
    newPos = board.copy()
    newPos.push(move)

    if newPos.is_check():
        return True

    if board.is_capture(move):
        # I feel like there are some complexities I miss
        return True

    for sq in newPos.attacks(move.to_square):
        if newPos.color_at(sq) == newPos.turn:
            print('Attack')


if __name__ == '__main__':
    board = chess.Board('r3k1nr/pp3pb1/1np2qp1/3p1p1p/3P3P/1PNQPPP1/P1P3B1/R1B1K2R b KQkq - 0 12')
    isForcingMove(board, chess.Move.from_uci('f5f4'))
