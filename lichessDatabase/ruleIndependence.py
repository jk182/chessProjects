import chess
import chess.pgn


def castlingFrequency(basePath: str, ratings: list) -> dict:
    """
    This calculates how frequently and on what moves players in different rating ranges usually castle
    """
    data = dict()
    for rating in ratings:
        # list of castling moves, [games where 0 players castled, 1 player castled, both players castled]
        data[rating] = [list(), [0, 0, 0]]
        with open(f'{basePath}{rating}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                whiteCastle = False
                blackCastle = False

                board = game.board()
                for ply, move in enumerate(game.mainline_moves()):
                    if 'O-O' in board.san(move):
                        data[rating][0].append(int(ply/2)+1)
                        if board.turn:
                            whiteCastle = True
                        else:
                            blackCastle = True
                    board.push(move)
                if whiteCastle and blackCastle:
                    data[rating][1][2] += 1
                elif whiteCastle or blackCastle:
                    data[rating][1][1] += 1
                else:
                    data[rating][1][0] += 1
    return data


def earlyQueenMoves(basePath: str, ratings: list, moveCutoff: int = 10) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = 0
        with open(f'{basePath}{rating}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()
                for ply, move in enumerate(game.mainline_moves()):
                    if board.san(move)[0] == 'Q':
                        data[rating] += 1
                    if ply/2 >= moveCutoff:
                        break
                    board.push(move)
    return data


def knightsOnTheRim(basePath: str, ratings: list) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = [0, 0]
        with open(f'{basePath}{rating}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()
                for move in game.mainline_moves():
                    data[rating][1] += 1
                    if board.san(move)[0] == 'N':
                        if move.uci()[2] == 'a' or move.uci()[2] == 'h':
                            data[rating][0] += 1
                    board.push(move)
    return data


def earlyRookPawnMoves(basePath: str, ratings: list, moveCutoff: int = 10) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = 0
        with open(f'{basePath}{rating}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()
                for ply, move in enumerate(game.mainline_moves()):
                    if board.san(move)[0] == 'a' or board.san(move)[0] == 'h':
                        data[rating] += 1
                    if ply/2 >= moveCutoff:
                        break
                    board.push(move)
    return data


def doubledPawns(basePath: str, ratings: list, moveCutoff: int = 20) -> dict:
    """
    This gets the number of moves where doubled pawns were present in positions
    """
    data = dict()
    for rating in ratings:
        data[rating] = [0, 0]
        with open(f'{basePath}{rating}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()
                for ply, move in enumerate(game.mainline_moves()):
                    data[rating][1] += 1
                    breakMap = False
                    pieceMap = board.piece_map()
                    for sq, piece in pieceMap.items():
                        if piece.symbol().lower() == 'p':
                            for s in range(sq+8, 64, 8):
                                if s in pieceMap.keys():
                                    if pieceMap[s] == pieceMap[sq]:
                                        data[rating][0] += 1
                                        breakMap = True
                        if breakMap:
                            break
                    if ply/2 >= moveCutoff:
                        break
                    board.push(move)
    return data


def isolatedPawns(basePath: str, ratings: list, moveCutoff: int = 20) -> dict:
    data = dict()
    for rating in ratings:
        data[rating] = [0, 0]
        with open(f'{basePath}{rating}.pgn', 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                board = game.board()
                for ply, move in enumerate(game.mainline_moves()):
                    data[rating][1] += 1
                    if ply/2 >= moveCutoff:
                        break
                    board.push(move)
    return data



if __name__ == '__main__':
    basePath = '../out/lichessDB/rating'
    ratings = [1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2700]

    """
    castlingData = castlingFrequency(basePath, ratings)
    print('Castling data:')
    for rating, data in castlingData.items():
        print(rating, sum(data[0])/len(data[0]), data[1])
    """

    """
    queenMoves = earlyQueenMoves(basePath, ratings)
    print('Queen move data:')
    for k, v in queenMoves.items():
        print(k, v)
    """

    """
    knightData = knightsOnTheRim(basePath, ratings)
    print('Knight data:')
    for k, v in knightData.items():
        print(k, v[0]/v[1])
    """

    """
    rookPawns = earlyRookPawnMoves(basePath, ratings)
    print('Early rook pawn moves:')
    for k, v in rookPawns.items():
        print(k, v)
    """

    dp = doubledPawns(basePath, ratings, moveCutoff=15)
    for k, v in dp.items():
        print(k, v[0]/v[1])
