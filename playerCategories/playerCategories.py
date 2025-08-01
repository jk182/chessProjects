import chess
from chess import pgn
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotting_helper


def countMaterial(board: chess.Board) -> list:
    """
    This function counts the material on the board for both sides
    """
    material = [0, 0]
    pieceValues = [1, 3, 3, 5, 9, 0]
    for color in [chess.WHITE, chess.BLACK]:
        if color == chess.WHITE:
            index = 0
        else:
            index = 1
        for pieceType in range(1, 6):
            material[index] += pieceValues[pieceType-1] * len(board.pieces(pieceType, color))
    return material


def isMaterialImbalance(board: chess.Board) -> bool:
    """
    This function checks if both sides have different material on the board.
    It can also return true if the material values is balanced, but the pieces are different (bishop vs knight or rook vs bishop+2 pawns)
    """
    for pieceType in range(1, 6):
        if len(board.pieces(pieceType, chess.WHITE)) != len(board.pieces(pieceType, chess.BLACK)):
            return True
    return False


def getPlayerData(pgnPath: str, playerName: str) -> dict:
    """
    This function gets data from the games for a specific player
    """
    perGameData = [
            'movesPerGame', 'kingsideCastling', 'queensideCastling', 'noCastling', 'oppositeSidesCastling', 'promotions']
    perMoveData = [
            'captures', 'recaptures', 'trades', 'centralMoves', 'flankMoves', 'movesInOppHalf', 'checks', 'inCheck', 
            'pawnMoves', 'aPawnMoves', 'bPawnMoves', 'cPawnMoves', 'dPawnMoves', 'ePawnMoves', 'fPawnMoves', 'gPawnMoves', 'hPawnMoves', 
            'pawnToRank5', 'pawnToRank6', 'pawnToRank7', 'pawnCaptures',
            'pieceMoves', 'knightMoves', 'bishopMoves', 'rookMoves', 'queenMoves', 'kingMoves', 'pieceCaptures', 'forwardPieceMoves', 'backwardPieceMoves', 
            'movesToEnemyKing', 'movesToEnemyKingMan', 'opponentKingMoves', 
            'materialUp', 'materialDown', 'avgMaterial', 'materialImbalance'
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
                materialIndex = 0
            elif playerName in game.headers["Black"]:
                playerColor = chess.BLACK
                materialIndex = 1
            else:
                print(f'Player not found: {game.headers["White"]}-{game.headers["Black"]}')
                continue

            totalGames += 1
            castling = [None, None]
            material = [39, 39]
            possibleImbalance = False
            wasCapture = False
            wasTrade = False

            board = game.board()
            for move in game.mainline_moves():
                startSq = move.from_square
                endSq = move.to_square
                isCapture = board.is_capture(move)
                rank = chess.square_rank(endSq) + 1
                oppKing = board.king(not playerColor)

                if board.turn == playerColor:
                    totalMoves += 1
                    data['movesPerGame'] += 1
                    data['avgMaterial'] += material[materialIndex]
                    piece = board.piece_at(startSq).piece_type

                    if endSq in centralSquares:
                        data['centralMoves'] += 1
                    if endSq in edgeSquares:
                        data['flankMoves'] += 1

                    if chess.square_distance(startSq, oppKing) > chess.square_distance(endSq, oppKing):
                        data['movesToEnemyKing'] += 1
                    if chess.square_manhattan_distance(startSq, oppKing) > chess.square_manhattan_distance(endSq, oppKing):
                        data['movesToEnemyKingMan'] += 1
                    
                    if board.gives_check(move):
                        data['checks'] += 1
                    if isCapture:
                        data['captures'] += 1
                        if wasCapture:
                            data['recaptures'] += 1
                    else:
                        wasCapture = False

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
                        pFile = files[chess.square_file(endSq)]
                        data[f'{pFile}PawnMoves'] += 1
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
                        castling[1] = 'k'
                    if board.is_queenside_castling(move):
                        castling[1] = 'q'
                    if board.piece_at(startSq).piece_type == chess.KING:
                        data['opponentKingMoves'] += 1
                    if isCapture:
                        if wasCapture:
                            wasTrade = True
                        wasCapture = True
                    else:
                        wasCapture = False
                
                board.push(move)
                if isCapture:
                    material = countMaterial(board)
                    if wasTrade and material[0] == material[1]:
                        data['trades'] += 1
                wasTrade = False

                if board.turn != playerColor:
                    if material[materialIndex] < material[(materialIndex+1)%2]:
                        data['materialDown'] += 1
                    if isMaterialImbalance(board):
                        possibleImbalance = True
                else:
                    if material[materialIndex] > material[(materialIndex+1)%2]:
                        data['materialUp'] += 1
                    if possibleImbalance:
                        possibleImbalance = False
                        if isMaterialImbalance(board):
                            data['materialImbalance'] += 1
                
            if castling[0] is None:
                data['noCastling'] += 1
            elif castling[1] is not None and castling[0] != castling[1]:
                data['oppositeSidesCastling'] += 1

    for d in perGameData:
        data[d] = data[d]/totalGames
    for d in perMoveData:
        data[d] = data[d]/totalMoves

    return data


def analyseData(pickleFiles: list):
    gData = list()
    labels = list()
    for pf in pickleFiles:
       with open(pf, 'rb') as f:
            d = pickle.load(f)
            labels = list(d.keys())
            print(pf, d)
            gData.append(list(d.values()))
    x = StandardScaler().fit_transform(gData)
    print(x.shape)
    pca = PCA(n_components=3)
    xPCA = pca.fit_transform(x)
    print(xPCA)
    print(pca.explained_variance_ratio_)
    
    correlationMatrix = [list()]
    for i in range(len(gData[0])):
        for k in range(len(xPCA[0])):
            correlationMatrix[-1].append(float(np.corrcoef([gData[j][i] for j in range(len(gData))], [xPCA[j][k] for j in range(len(xPCA))])[0,1]))
        print(labels[i], correlationMatrix[-1])
        correlationMatrix.append([])

    """
    fig, ax = plt.subplots(2, 2, figsize=(10, 10))
    for (a, b, x, y) in [(0, 0, 0, 1), (0, 1, 2, 1), (1, 0, 0, 2)]:
        for i, s in enumerate(xPCA):
            ax[a, b].scatter(s[x], s[y], label=pickleFiles[i].split('/')[-1][:-7])
            ax[a, b].annotate(pickleFiles[i].split('/')[-1][:-7], (s[x], s[y]))
            ax[a, b].axhline(y=0, color='black', linewidth=0.5)
            ax[a, b].axvline(x=0, color='black', linewidth=0.5)
            ax[a, b].set_facecolor(plotting_helper.getColor('background'))
            ax[a, b].set(xlabel=x, ylabel=y)
    """
    universal = ['Fischer', 'Botvinnik']
    attacking = ['Polgar', 'Shirov', 'Topalov', 'Kasparov', 'Tal', 'Spassky', 'Bronstein']
    usedLabels = list()

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor(plotting_helper.getColor('background'))
    for i, s in enumerate(xPCA):
        name = pickleFiles[i].split('/')[-1][:-7].capitalize()
        if name in universal:
            color = plotting_helper.getColor('purple')
            label = 'universal'
        elif name in attacking:
            color = plotting_helper.getColor('orange')
            label = 'attacking'
        else:
            color = plotting_helper.getColor('blue')
            label = 'positional'
        if label in usedLabels:
            label = ''
        else:
            usedLabels.append(label)
        ax.scatter(s[0], s[1], color=color, label=label)
        ax.annotate(name, (s[0]-0.075 * len(name), s[1]-0.3))
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axvline(x=0, color='black', linewidth=0.5)
    ax.set_xlabel('Component 1')
    ax.set_ylabel('Component 2')
    plt.title('Categorisation of different players')
    ax.legend()
    fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.9)
    plt.savefig('../out/categories.png', dpi=400)
    plt.show()

    """
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    for i, s in enumerate(xPCA):
        ax.scatter(s[0], s[1], s[2], label=pickleFiles[i].split('/')[-1][:-7])
    ax.legend()
    plt.show()
    """


if __name__ == '__main__':
    capa = '../out/games/capablanca.pgn'
    alekhine = '../out/games/alekhine.pgn'
    tal = '../out/games/tal.pgn'
    smyslov = '../out/games/smyslov.pgn'
    karpov = '../out/games/karpov.pgn'
    kasparov = '../out/games/kasparov.pgn'
    botvinnik = '../out/games/botvinnik.pgn'
    bronstein = '../out/games/bronstein.pgn'
    andersson = '../out/games/andersson.pgn'
    polgar = '../out/games/polgar.pgn'
    morphy = '../out/games/morphy.pgn'
    adams = '../out/games/adams.pgn'
    shirov = '../out/games/shirov.pgn'
    topalov = '../out/games/topalov.pgn'
    spassky = '../out/games/spassky.pgn'
    fischer = '../out/games/fischer.pgn'
    petrosian = '../out/games/petrosian.pgn'
    carlsen2013 = '../out/games/carlsen2013.pgn'
    carlsen2019 = '../out/games/carlsen2019.pgn'
    
    """
    with open('../out/categories/capablanca.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(capa, 'Capablanca'), f)
    with open('../out/categories/alekhine.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(alekhine, 'Alekhine'), f)
    with open('../out/categories/tal.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(tal, 'Tal, M'), f)
    with open('../out/categories/smyslov.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(smyslov, 'Smyslov'), f)
    with open('../out/categories/karpov.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(karpov, 'Karpov'), f)
    with open('../out/categories/kasparov.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(kasparov, 'Kasparov'), f)
    with open('../out/categories/botvinnik.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(botvinnik, 'Botvinnik'), f)
    with open('../out/categories/bronstein.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(bronstein, 'Bronstein'), f)
    with open('../out/categories/andersson.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(andersson, 'Andersson'), f)
    with open('../out/categories/polgar.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(polgar, 'Polgar'), f)
    with open('../out/categories/morphy.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(morphy, 'Morphy'), f)
    with open('../out/categories/adams.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(adams, 'Adams'), f)
    with open('../out/categories/shirov.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(shirov, 'Shirov'), f)
    with open('../out/categories/topalov.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(topalov, 'Topalov'), f)
    with open('../out/categories/spassky.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(spassky, 'Spassky'), f)
    with open('../out/categories/fischer.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(fischer, 'Fischer'), f)
    with open('../out/categories/petrosian.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(petrosian, 'Petrosian'), f)
    with open('../out/categories/carlsen2013.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(carlsen2013, 'Carlsen'), f)
    with open('../out/categories/carlsen2019.pickle', 'wb+') as f:
        pickle.dump(getPlayerData(carlsen2019, 'Carlsen'), f)
    """
    # Morphy is a complete outlier
    pickleFiles = ['../out/categories/smyslov.pickle', '../out/categories/tal.pickle', '../out/categories/karpov.pickle', '../out/categories/kasparov.pickle', 
            '../out/categories/botvinnik.pickle', '../out/categories/bronstein.pickle', '../out/categories/andersson.pickle', '../out/categories/polgar.pickle', '../out/categories/adams.pickle', '../out/categories/shirov.pickle', 
            '../out/categories/topalov.pickle', '../out/categories/spassky.pickle', '../out/categories/fischer.pickle', '../out/categories/petrosian.pickle']
    analyseData(pickleFiles)
