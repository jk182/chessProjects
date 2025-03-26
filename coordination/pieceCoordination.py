import chess


def calculateCoordination(board: chess.Board) -> float:
    return 1


def calculateDefenseScore(board: chess.Board, pieceSq: int) -> float:
    color = board.color_at(pieceSq)
    pieceMap = board.piece_map()
    total = 0
    for square in board.attacks(pieceSq) & board.occupied:
        if square in pieceMap.keys():
            attackedPiece = pieceMap[square]
            if attackedPiece.color == color and 2 <= attackedPiece.piece_type:
                total += 1
    return total


def countAttackedSquares(board: chess.Board, color: chess.Color) -> float:
    total = 0
    for square in chess.SQUARES:
        total += len(board.attackers(color, square))
    return total


def findBatteries(board: chess.Board, color: chess.Color):
    pieceMap = board.piece_map()
    for square, piece in pieceMap.items():
        if piece.piece_type == chess.BISHOP:
            for sq in board.attacks(square):
                if sq in pieceMap.keys():
                    if pieceMap[sq].piece_type == chess.QUEEN:
                        print('Queen-bishop battery')
            print(piece)


if __name__ == '__main__':
    board = chess.Board('2bqr1k1/1p3ppp/p2b1n2/3p4/8/1P2PN2/PB2NPPP/3Q1RK1 b - - 1 17')
    dragon = chess.Board('rnbq1rk1/pp2ppbp/3p1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R b KQ - 2 8')
    # for piece in chess.SquareSet(board.occupied):
        # print(calculateDefenseScore(board, piece))
    # print(countAttackedSquares(board, board.turn))
    findBatteries(dragon, chess.WHITE)
