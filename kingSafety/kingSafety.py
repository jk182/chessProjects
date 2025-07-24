import chess


def getPawnCover(board: chess.Board) -> list:
    """
    This fucntion gets all the pawns which cover each side's king
    board: chess.Board
        The position
    return -> list
        A list containing a list of the pawns covering the king for each side
    """
    pawns = [list(), list()]
    for color in [chess.WHITE, chess.BLACK]:
        if color == chess.WHITE:
            index = 0
        else:
            index = 1

        king = board.king(color)
        kingFile = chess.square_file(king)
        files = [kingFile]
        if kingFile > 0:
            files.append(kingFile-1)
        if kingFile < 7:
            files.append(kingFile+1)
        for pawn in board.pieces(chess.PAWN, color):
            if chess.square_file(pawn) in files:
                pawns[index].append(pawn)
    return pawns


def evaluatePawnCover(board: chess.Board) -> list:
    """
    This evaluates the pawn shield of both sides in a position
    board: chess.Board
        The position
    return -> list
        The score of the pawn shield for both sides (only positive)
    """
    pawns = getPawnCover(board)
    # The values each covering pawn provides for the king
    coverValues = [3, 2, 1]
    openFileLoss = [3, 2]
    ks = [0, 0]
    for color in [chess.WHITE, chess.BLACK]:
        files = set()
        if color:
            index = 0
        else:
            index = 1
        king = board.king(color)
        kingFile = chess.square_file(king)
        kingRank = chess.square_rank(king)
        for pawn in pawns[index]:
            pawnRank = chess.square_rank(pawn)
            files.add(chess.square_file(pawn))
            for off in range(1, 4):
                if color:
                    if pawnRank == kingRank+off:
                        ks[0] += coverValues[off-1]
                else:
                    if pawnRank == kingRank-off:
                        ks[1] += coverValues[off-1]
        if kingFile not in files:
            ks[index] -= openFileLoss[0]
        if kingFile > 0 and kingFile-1 not in files:
            ks[index] -= openFileLoss[1]
        if kingFile < 7 and kingFile+1 not in files:
            ks[index] -= openFileLoss[1]
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
    # Giving each piece an attacking value
    pieceValues = [1, 1, 1, 1, 1, 1]
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
                        ks[index] -= pieceValues[pieceType-1]
    return ks


if __name__ == '__main__':
    fen = 'rn1qk2r/1p2bpp1/p2pbn2/4p2p/4P3/1NN1BP2/PPPQ2PP/2KR1B1R b kq - 1 10'
    fen2 = 'rnbqkbnr/pppp1p1p/8/8/2B1Pp2/5p2/PPPP2PP/RNBQ1RK1 w kq - 0 6'
    board = chess.Board(fen2)
    print(evaluatePawnCover(board))
    # print(attackingPieces(board))
