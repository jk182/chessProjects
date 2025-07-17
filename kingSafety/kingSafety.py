import chess


def pawnShield(board: chess.Board) -> list:
    """
    This evaluates the pawn shield of both sides in a position
    board: chess.Board
        The position
    return -> list
        The score of the pawn shield for both sides (only positive)
    """
    # TODO: add pawns which aren't directly in front of the king
    ks = [0, 0]
    for color in [chess.WHITE, chess.BLACK]:
        king = board.king(color)
        pawns = list()
        for square in board.attacks(king):
            if board.piece_type_at(square) == chess.PAWN and board.color_at(square) == color:
                pawns.append(square)
        for p in pawns:
            if color == chess.WHITE:
                if p >= king + 7 and p <= king + 9:
                    ks[0] += 1
                if p == king + 8:
                    ks[0] += 1
            else:
                if p <= king - 7 and p >= king - 9:
                    ks[1] += 1
                if p == king - 8:
                    ks[1] += 1
        if color == chess.WHITE and king in [0, 7]:
            ks[0] += 1
        if color == chess.BLACK and king in [56, 63]:
            ks[1] += 1
    return ks


def attackingPieces(board: chess.Board) -> list:
    """
    This evaluates the attackers against the king
    board: chess.Board
        The position
    return -> list
        The king saftey score for both colors, which will be negative for the attackers
    """
    ks = [0, 0]
    for color in [chess.WHITE, chess.BLACK]:
        king = board.king(color)
        kingSquares = board.attacks(king)
        kingSquares.add(king)
        if color:
            index = 1
        else:
            index = 0

        for pieceType in range(1, 7):
            for piece in board.pieces(pieceType, not color):
                for square in board.attacks(piece):
                    if square in kingSquares:
                        print(square)
                        ks[index] -= 1
    return ks


if __name__ == '__main__':
    fen = 'rn1qk2r/1p2bpp1/p2pbn2/4p2p/4P3/1NN1BP2/PPPQ2PP/2KR1B1R b kq - 1 10'
    fen2 = 'rnbqkbnr/pppp1p1p/8/8/2B1Pp2/5p2/PPPP2PP/RNBQ1RK1 w kq - 0 6'
    board = chess.Board(fen2)
    print(pawnShield(board))
    print(attackingPieces(board))
