import chess
from chess import pgn


def getPlayerData(pgnPath: str, playerName: str) -> dict:
    """
    This function gets data from the games for a specific player
    """
    perGameData = [
            'movesPerGame', 'kingsideCastling', 'queensideCastling', 'noCastling', 'oppositeSidesCastling']
    perMoveData = [
            'captures', 'centralMoves', 'flankMoves', 'movesInOppHalf', 'checks', 'inCheck', 
            'pawnMoves', 'aPawnMoves', 'bPawnMoves', 'cPawnMoves', 'dPawnMoves', 'ePawnMoves', 'fPawnMoves', 'gPawnMoves', 'hPawnMoves', 
            'pawnToRank5', 'pawnToRank6', 'pawnToRank7', 'promotions', 'pawnCaptures',
            'pieceMoves', 'knightMoves', 'bishopMoves', 'rookMoves', 'queenMoves', 'kingMoves', 'pieceCaptures', 'forwardPieceMoves', 'backwardPieceMoves'
            ]
    data = dict()
    for d in perGameData:
        data[d] = 0
    for d in perMoveData:
        data[d] = 0

    totalMoves = 0
    totalGames = 0
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    centralSquares = [chess.C3, chess.D3, chess.E3, chess.F3, chess.C4, chess.D4, chess.E4, chess.F4, chess.C5, chess.D5, chess.E5, chess.F5, chess.C6, chess.D6, chess.E6, chess.F6]
    edgeSquares = [chess.A1, chess.A2, chess.A3, chess.A4, chess.A5, chess.A6, chess.A7, chess.A8, 
                   chess.H1, chess.H2, chess.H3, chess.H4, chess.H5, chess.H6, chess.H7, chess.H8]

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if playerName in game.headers["White"]:
                playerColor = chess.WHITE
            elif playerName in game.headers["Black"]:
                playerColor = chess.BLACK
            else:
                print('Player not found')
                continue

            totalGames += 1
            castling = [None, None]

            board = game.board()
            for move in game.mainline_moves():
                startSq = move.from_square
                endSq = move.to_square
                isCapture = board.is_capture(move)
                rank = chess.square_rank(endSq) + 1

                if board.turn == playerColor:
                    totalMoves += 1
                    data['movesPerGame'] += 1
                    piece = board.piece_at(startSq).piece_type

                    if endSq in centralSquares:
                        data['centralMoves'] += 1
                    if endSq in edgeSquares:
                        data['flankMoves'] += 1
                    
                    if board.gives_check(move):
                        data['checks'] += 1
                    if isCapture:
                        data['captures'] += 1

                    if board.is_kingside_castling(move):
                        data['kingsideCastling'] += 1
                        castling[0] = 'k'
                    if board.is_queenside_castling(move):
                        data['queensideCastling'] += 1
                        castling[0] = 'q'

                    if (playerColor == chess.WHITE and rank >= 5) or (playerColor == chess.BLACK and rank <= 4):
                        data['movesInOppHalf'] += 1

                    if piece != chess.PAWN:
                        data['pieceMoves'] += 1
                        if isCapture:
                            data['pieceCaptures'] += 1
                        if chess.square_rank(startSq) < chess.square_rank(endSq):
                            data['forwardPieceMoves'] += 1
                        elif chess.square_rank(startSq) > chess.square_rank(endSq):
                            data['backwardPieceMoves'] += 1
                    if piece == chess.PAWN:
                        data['pawnMoves'] += 1
                        if isCapture:
                            data['pawnCaptures'] += 1
                        file = files[chess.square_file(endSq)]
                        data[f'{file}PawnMoves'] += 1
                        if playerColor == chess.WHITE:
                            if 5 <= rank <= 7:
                                data[f'pawnToRank{rank}'] += 1
                            elif rank == 8:
                                data['promotions'] += 1
                        else:
                            if 4 <= rank <= 2:
                                data[f'pawnToRank{9-rank}'] += 1
                            elif rank == 1:
                                data['promotions'] += 1
                    elif piece == chess.KNIGHT:
                        data['knightMoves'] += 1
                    elif piece == chess.BISHOP:
                        data['bishopMoves'] += 1
                    elif piece == chess.ROOK:
                        data['rookMoves'] += 1
                    elif piece == chess.QUEEN:
                        data['queenMoves'] += 1
                    elif piece == chess.KING:
                        data['kingMoves'] += 1
                else:
                    if board.gives_check(move):
                        data['inCheck'] += 1
                    if board.is_kingside_castling(move):
                        castling[0] = 'k'
                    if board.is_queenside_castling(move):
                        castling[0] = 'q'


                board.push(move)
        if castling[0] is None:
            data['noCastling'] += 1
        elif castling[1] is not None and castling[0] != castling[1]:
            data['oppositeSidesCastling'] += 1

    for d in perGameData:
        data[d] = round(data[d]/totalGames, 3)
    for d in perMoveData:
        data[d] = round(data[d]/totalMoves, 3)

    return data


if __name__ == '__main__':
    capa = '../out/games/capablancaFiltered2.pgn'
    alekhine = '../out/games/alekhine27-40.pgn'
    print(getPlayerData(capa, 'Capablanca'))
    print(getPlayerData(alekhine, 'Alekhine'))
