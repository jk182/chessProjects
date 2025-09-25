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
        king = list(board.pieces(6, not color))[0]
        kingSquares = board.attacks(king)
        kingSquares.add(king)
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
                        if square in kingSquares:
                            # counting the attacked squares around the enemy king extra
                            activity[index] += 1
                        if color == chess.WHITE and square >= 32:
                            # counting the attacked squares in the opponent's half extra
                            activity[index] += 1
                        elif color == chess.BLACK and square <= 31:
                            activity[index] += 1
    return activity


def calcGenMean(data: list, p: int = 1):
    """
    This calculates the generalized mean for a list of data
    """
    mean = sum([d**p for d in data]) * (1/len(data))
    return mean**(1/p)


def updatedPieceActivity(fen: str, includeKing: bool = True) -> list:
    """
    This is an updated version of the piece activity score
    """
    debug = True
    # TODO: check the correct mapping to squares
    boardValues = [0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8,
                   0.7, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.7,
                   0.6, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.6,
                   0.6, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.6,
                   0.5, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.5,
                   0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4,
                   0.3, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3,
                   0.2, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.2]
    kingMask = [0.2, 0.2, 0.2, 
                0.3, 0.5, 0.3, 
                0.3, 0.3, 0.3]
    kingMoveIndices = [-9, -8, -7, -1, 0, 1, 7, 8, 9]

    boardMeanP = 2

    activity = [0, 0]
    board = chess.Board(fen)
    for color in [chess.WHITE, chess.BLACK]:
        if debug:
            if color:
                print('White')
            else:
                print('Black')
        pieceActivities = list()
        king = list(board.pieces(6, not color))[0]
        kingSquares = board.attacks(king)
        kingSquares.add(king)

        piecesColor = chess.SquareSet(board.occupied_co[color])
        bishops = board.pieces(3, color)
        rooks = board.pieces(4, color)
        queens = board.pieces(5, color)
        
        if color:
            colorIndex = 0
        else:
            colorIndex = 1
        for pieceType in range(2, 7):
            if pieceType == 6 and not includeKing:
                continue
            for piece in board.pieces(pieceType, color):
                attackedSquares = board.attacks(piece)
                attackValues = list()
                for square in attackedSquares:
                    if ((pieceType == 4 or pieceType == 5) and (square in rooks or square in queens)) or ((pieceType == 3 or pieceType == 5) and (square in bishops or square in queens)):
                        batterySquares = chess.SquareSet(chess.ray(piece, square)).intersection(board.attacks(square))
                        for s in batterySquares:
                            if s in piecesColor:
                                continue
                            kingBoost = 0
                            if s in kingSquares:
                                index = kingMoveIndices.index(s-king)
                                if color:
                                    kingBoost = kingMask[index]
                                else:
                                    kingBoost = kingMask[8-index]
                            if color:
                                attackValues.append(min(boardValues[63-s]+kingBoost, 1))
                            else:
                                attackValues.append(min(boardValues[s]+kingBoost, 1))
                    # Don't count attacks on onw pieces
                    if square in piecesColor:
                        continue
                    kingBoost = 0
                    if square in kingSquares:
                        index = kingMoveIndices.index(square-king)
                        if color:
                            kingBoost = kingMask[index]
                        else:
                            kingBoost = kingMask[8-index] # TODO: is the black-white flipping correct?
                    if color:
                        attackValues.append(min(boardValues[63-square]+kingBoost, 1))
                    else:
                        attackValues.append(min(boardValues[square]+kingBoost, 1))

                # Add all possible moves for knights and kings
                if pieceType in [2, 6]:
                    attackValues.extend([0]*(8-len(attackValues)))

                if len(attackValues) == 0:
                    attackValues.append(0)

                if debug:
                    print(chess.piece_symbol(pieceType), chess.SQUARE_NAMES[piece])
                    print(calcGenMean(attackValues, 2))

                pieceActivities.append(calcGenMean(attackValues, 2))
        activity[colorIndex] = calcGenMean(pieceActivities, boardMeanP)
    return activity


def plotPieceActivity(pgnPath: str, title: str = None, filename: str = None):
    """
    This function plots the piece activity for White and Black in a given game.
    pgnPath: str
        Path to the PGN file of the game
    title: str
        Title of the plot (usually the players of the game)
    filname: str
        The name of the file to which the graph will be saved.
        If no name is given, the graph will be shown instead of saved.
    """
    white = list()
    black = list()
    players = list()
    gameNr = 0
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            gameNr += 1
            w = game.headers['White']
            b = game.headers['Black']
            if ',' in w:
                w = w.split(',')[0]
            elif ' ' in w:
                w = w.split(' ')[-1]
            if ',' in b:
                b = b.split(',')[0]
            elif ' ' in b:
                b = b.split(' ')[-1]
            players.append(w)
            players.append(b)

            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                # activity = calculatePieceActivity(board.fen())
                activity = updatedPieceActivity(board.fen())
                white.append(activity[0])
                black.append(activity[1])

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(range(1, len(white)+1), white, color='#f8a978', label=f"{players[0]}'s piece activity")
            ax.plot(range(1, len(black)+1), black, color='#111111', label=f"{players[1]}'s piece activity")

            ax.set_facecolor('#e6f7f2')
            ax.set_xlabel('Move number')
            ax.set_ylabel('Piece activity')
            ax.set_xlim(1, len(white))
            ax.set_ylim(0)
            ax.set_xticks(list(range(1, len(white)))[::10])
            ax.set_xticklabels([i//2 for i in range(len(white)-1)[::10]])
            plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
            if title:
                plt.title(title)
            else:
                plt.title(f"Game {gameNr} Piece Activity")
            ax.legend()

            if filename:
                plt.savefig(f'{filename}G{gameNr}.png', dpi=500)
            else:
                plt.show()
            white = list()
            black = list()
            players = list()


if __name__ == '__main__':
    fen = 'r6r/pp1qnkpp/5p2/3p4/3N4/8/PP2QPPP/2R1R1K1 w - - 2 19'
    fens = ['r6r/pp1qnkpp/5p2/3p4/3N4/8/PP2QPPP/2R1R1K1 w - - 2 19', 
            '4r1k1/3n1pp1/2R3N1/Q2p4/P6p/1P2rPqP/3RB1P1/5K2 b - - 2 35', 
            '3q2k1/pb1rbp2/4p1p1/3n2Np/1p1Q3P/6P1/PP1BPPB1/5RK1 w - - 1 26', 
            '1r6/p1q1k1p1/7p/4pp2/5nb1/P1P5/P1QP1PPP/R1B2RK1 b - - 4 23', 
            '6k1/2rnn1p1/p1p2p1p/4p3/1B2P2P/P4NP1/5P2/3R2K1 b - - 3 28']
    fens2 = ['2b2k2/rpp1q1pp/5p2/b1P1pP2/4N1P1/r3P2P/2Q4K/1R1R1B2 w - - 0 1', 
             '5k2/rpp1q1pp/5p2/bQP1pP2/4N1P1/4P2P/7K/3R4 b - - 0 4', 
             'r5rk/1ppb2bp/n2p1nq1/3P1p2/1PP1pP2/2N1B2P/2BQN1P1/1R3R1K w - - 0 1', 
             'rb1q1r1k/1p4p1/1Pp1bn1p/p1P1pn2/3pN2P/P2P1PP1/1NQB2BK/4RR2 w - - 0 1', 
             '1rr2bk1/1p3p1p/p1n1p1p1/2Nq4/1P1P4/P3BP2/2Q3PP/2RR2K1 w - - 0 1', 
             'r3k2r/pp2qppp/2b1p3/2n1P3/3N4/2P5/P1B1QPPP/R2R2K1 b kq - 0 1']
    pgn = '../resources/steinitz-vonBardeleben.pgn'
    # plotPieceActivity(pgn, title='Steinitz-von Bardeleben, 1895')
    # plotPieceActivity('../resources/fedoseev-carlsen.pgn', title='Fedoseev-Carlsen, 2021')
    # plotPieceActivity('../resources/huzman-aronian.pgn', title='Huzman-Aronian, 2010')
    for fen in fens2:
        print(updatedPieceActivity(fen, includeKing=False))
