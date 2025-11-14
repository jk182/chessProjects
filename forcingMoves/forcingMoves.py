import chess
import chess.pgn

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper


def generateDiagonals() -> list:
    diagonals = list()
    for sq in range(64):
        diag = chess.SquareSet(0)
        if sq % 8 != 7:
            if sq < 56:
                diag |= chess.ray(sq, sq+9)
            if sq >= 8:
                diag |= chess.ray(sq, sq-7)
        if sq % 8 != 0:
            if sq < 56:
                diag |= chess.ray(sq, sq+7)
            if sq >= 8:
                diag |= chess.ray(sq, sq-9)
        diagonals.append(diag)
    return diagonals


def isThreat(board: chess.Board, move: chess.Move) -> bool:
    newPos = board.copy()
    newPos.push(move)
    # Threat detection
    attackingPiece = board.piece_type_at(move.from_square)
    pinBB = newPos.pin(board.turn, move.to_square)
    for sq in newPos.attacks(move.to_square) & newPos.occupied_co[newPos.turn] & pinBB:
        attackedPiece = newPos.piece_type_at(sq)
        if attackedPiece > attackingPiece:
            return True
        if not newPos.attackers(newPos.turn, sq):
            return True

    # Discovered attacks
    fr = chess.BB_FILES[chess.square_file(move.from_square)] | chess.BB_RANKS[chess.square_rank(move.from_square)]
    for piece in board.pieces(chess.BISHOP, board.turn) | (board.pieces(chess.ROOK, board.turn) & fr) | board.pieces(chess.QUEEN, board.turn):
        ray = chess.SquareSet.ray(move.from_square, piece)
        if not ray:
            continue

        between = chess.SquareSet.between(move.from_square, piece)
        pinBB = newPos.pin(board.turn, piece)
        for sq in (chess.SquareSet(newPos.occupied) & ray & newPos.occupied_co[newPos.turn] & pinBB) & ~between:
            if piece in newPos.attackers(board.turn, sq) and move.from_square in chess.SquareSet.between(sq, piece):
                attackingPiece = board.piece_type_at(piece)
                attackedPiece = newPos.piece_type_at(sq)
                if attackedPiece > attackingPiece:
                    return True
                if not newPos.attackers(newPos.turn, sq):
                    return True

    # Mate in one threats
    newPos.turn = not newPos.turn
    for move in newPos.legal_moves:
        newPos.push(move)
        if newPos.is_checkmate():
            return True
        newPos.pop()
    return False


def isForcingMove(board: chess.Board, move: chess.Move, lastCaptureSquare: int) -> bool:
    """
    This function determines whether the given move is a forcing move in the position
    """

    if board.gives_check(move):
        return True

    if board.is_capture(move):
        if lastCaptureSquare is None:
            return True
        elif move.to_square != lastCaptureSquare:
            # Removing recaptures
            return True

    return isThreat(board, move)


def countForcingMoves(pgnPaths: list) -> dict:
    """
    This function counts the number of forcing moves for each player
    """
    fMoves = dict()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                lastCaptureSquare = None
                for color in ["White", "Black"]:
                    if game.headers[color] not in fMoves.keys():
                        fMoves[game.headers[color]] = [0, 0]

                board = game.board()
                for move in game.mainline_moves():
                    if board.turn:
                        player = game.headers["White"]
                    else:
                        player = game.headers["Black"]
                    if isForcingMove(board, move, lastCaptureSquare):
                        fMoves[player][0] += 1
                    fMoves[player][1] += 1
                    if board.is_capture(move):
                        lastCaptureSquare = move.to_square
                    board.push(move)
    return fMoves


def getForcingMovesPerPlayer(pgnPaths: list, players: list) -> dict:
    """
    This counts the forcing moves for different players. 
    The players list contains the name of each player and the first player will be searched in the first PGN and so on
    """
    fMoves = dict()
    for i, pgnPath in enumerate(pgnPaths):
        with open(pgnPath, 'r') as pgn:
            moveData = [0, 0]
            while game := chess.pgn.read_game(pgn):
                lastCaptureSquare = None
                if players[i] in game.headers["White"]:
                    color = True
                elif players[i] in game.headers["Black"]:
                    color = False
                else:
                    continue

                board = game.board()
                for move in game.mainline_moves():
                    if board.turn == color:
                        moveData[1] += 1
                        if isForcingMove(board, move, lastCaptureSquare):
                            moveData[0] += 1
                    if board.is_capture(move):
                        lastCaptureSquare = move.to_square
                    board.push(move)
        fMoves[players[i]] = moveData
    return fMoves


def getSplitForcingMoves(pgnPaths: list, players: list) -> dict:
    fMoves = dict()
    for i, pgnPath in enumerate(pgnPaths):
        with open(pgnPath, 'r') as pgn:
            moveData = [0, 0, 0, 0]
            while game := chess.pgn.read_game(pgn):
                lastCaptureSquare = None
                if players[i] in game.headers["White"]:
                    color = True
                elif players[i] in game.headers["Black"]:
                    color = False
                else:
                    continue

                board = game.board()
                for move in game.mainline_moves():
                    if board.turn == color:
                        updated = False
                        moveData[3] += 1
                        if board.gives_check(move):
                            moveData[0] += 1
                            updated = True
                        elif board.is_capture(move):
                            if lastCaptureSquare is None:
                                moveData[1] += 1
                                updated = True
                            elif move.to_square != lastCaptureSquare:
                                # Removing recaptures
                                moveData[1] += 1
                                updated = True
                        if isThreat(board, move) and not updated:
                            moveData[2] += 1
                    if board.is_capture(move):
                        lastCaptureSquare = move.to_square
                    board.push(move)
        fMoves[players[i]] = moveData
    return fMoves


if __name__ == '__main__':
    board = chess.Board('r3k1nr/pp3pb1/1np2qp1/3p1p1p/3P3P/1PNQPPP1/P1P3B1/R1B1K2R b KQkq - 0 12')
    # isForcingMove(board, chess.Move.from_uci('f5f4'))
    pgns = ['../resources/games/alekhine.pgn', '../resources/games/capablanca.pgn', '../resources/games/tal.pgn', '../resources/games/botvinnik.pgn', '../resources/games/smyslov.pgn', '../resources/games/kasparov.pgn', '../resources/games/karpov.pgn']
    pgnsTest = ['../resources/games/kasparov.pgn', '../resources/games/karpov.pgn']
    """
    data = countForcingMoves(pgns)
    for k, v in data.items():
        if 'Kasparov' in k or 'Karpov' in k or 'Tal' in k or 'Botvinnik' in k:
            print(k, v, v[0]/v[1])
    """
    # global DIAGONALS = generateDiagonals()
    players = ['Alekhine', 'Capablanca', 'Tal', 'Botvinnik', 'Smyslov', 'Kasparov', 'Karpov']
    plotData = list()
    # fMoveData = getForcingMovesPerPlayer(pgnsTest, ['Kasparov', 'Karpov'])
    """
    fMoveData = getForcingMovesPerPlayer(pgns, players)
    for k, v in fMoveData.items():
        print(k, v, v[0]/v[1])
        plotData.append([v[0]/v[1]])
    plotting_helper.plotPlayerBarChart(plotData, players, 'Relative number of forcing moves', 'Relative number of forcing moves for different players', ['Forcing moves'], filename='../out/forcingMoves.png')
    """
    data = getSplitForcingMoves(pgns, players)
    for k, v in data.items():
        # print(k, v[0]/v[3], v[1]/v[3], v[2]/v[3])
        plotData.append([v[i]/v[3] for i in range(3)])
    plotting_helper.plotPlayerBarChart(plotData, players, 'Relative number of moves', 'Checks, captures and threats for different players', ['Checks', 'Captures', 'Threats'], filename='../out/CCT.png')
