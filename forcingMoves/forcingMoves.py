import chess
import chess.pgn


def isForcingMove(board: chess.Board, move: chess.Move, captureHistory: list) -> bool:
    """
    This function determines whether the given move is a forcing move in the position
    """

    if board.gives_check(move):
        return True

    if board.is_capture(move):
        if captureHistory:
            if move.to_square != captureHistory[-1].to_square:
                # Removing recaptures
                return True
        else:
            return True

    newPos = board.copy()
    newPos.push(move)
    # Threat detection
    attackingPiece = board.piece_type_at(move.from_square)
    for sq in newPos.attacks(move.to_square):
        if newPos.color_at(sq) == newPos.turn:
            attackedPiece = newPos.piece_type_at(sq)
            if attackedPiece not in newPos.pin(board.turn, move.to_square):
                # removing attacks created by pinned pieces
                continue
            if attackedPiece > attackingPiece:
                return True
            if len(newPos.attackers(newPos.turn, sq)) == 0:
                return True

    # Discovered attacks
    for piece in board.pieces(chess.BISHOP, board.turn) | board.pieces(chess.ROOK, board.turn) | board.pieces(chess.QUEEN, board.turn):
        ray = chess.SquareSet.ray(move.from_square, piece)
        if not ray:
            continue

        between = chess.SquareSet.between(move.from_square, piece)
        for sq in chess.SquareSet(newPos.occupied) & ray:
            if sq not in between and newPos.color_at(sq) == newPos.turn:
                if piece in newPos.attackers(board.turn, sq) and move.from_square in chess.SquareSet.between(sq, piece):
                    attackingPiece = board.piece_type_at(piece)
                    attackedPiece = newPos.piece_type_at(sq)
                    if attackedPiece > attackingPiece:
                        return True
                    if len(newPos.attackers(newPos.turn, sq)) == 0:
                        return True

    return False


def countForcingMoves(pgnPaths: list) -> dict:
    """
    This function counts the number of forcing moves for each player
    """
    fMoves = dict()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                captureHistory = list()
                for color in ["White", "Black"]:
                    if game.headers[color] not in fMoves.keys():
                        fMoves[game.headers[color]] = [0, 0]

                board = game.board()
                for move in game.mainline_moves():
                    if board.turn:
                        player = game.headers["White"]
                    else:
                        player = game.headers["Black"]
                    if isForcingMove(board, move, captureHistory):
                        fMoves[player][0] += 1
                    fMoves[player][1] += 1
                    board.push(move)
                    captureHistory.append(move)
    return fMoves


if __name__ == '__main__':
    board = chess.Board('r3k1nr/pp3pb1/1np2qp1/3p1p1p/3P3P/1PNQPPP1/P1P3B1/R1B1K2R b KQkq - 0 12')
    # isForcingMove(board, chess.Move.from_uci('f5f4'))
    pgns = ['../resources/games/kasparov.pgn', '../resources/games/karpov.pgn', '../resources/games/tal.pgn', '../resources/games/botvinnik.pgn']
    data = countForcingMoves(pgns)
    for k, v in data.items():
        if 'Kasparov' in k or 'Karpov' in k or 'Tal' in k or 'Botvinnik' in k:
            print(k, v, v[0]/v[1])
