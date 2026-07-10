import chess
import chess.pgn
import io
import polars as pl
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper
import functions
import matplotlib.pyplot as plt


def extractGames(ratingBands: list, gamesPerBand: int, timeControl: str, maxRatingDiff: int = 50, outPath: str = '../out/lichessDB/rating', onlyAnalysed: bool = False):
    pgns = [""] * len(ratingBands)
    nGames = [0] * len(ratingBands)
    currentPGN = ""
    wElo = None
    bElo = None
    ratingIndex = None
    useGame = True

    while True:
        if min(nGames) >= gamesPerBand:
            break

        line = input().strip()

        if not line:
            continue

        currentPGN = f'{currentPGN}{line}\n'

        ls = line.split('"')

        if 'WhiteElo' in ls[0]:
            wElo = int(ls[1])
        if 'BlackElo' in ls[0]:
            bElo = int(ls[1])

        if 'TimeControl' in ls[0]:
            if ls[1] != timeControl:
                useGame = False

        if line[0] == '1':
            if wElo is not None and bElo is not None:
                if abs(wElo-bElo) <= maxRatingDiff and (avgElo := (wElo+bElo)/2) > min(ratingBands):
                    ratingIndex = len(ratingBands) - 1
                    for i, rating in enumerate(ratingBands[:-1]):
                        if avgElo >= rating and avgElo < ratingBands[i+1]:
                            ratingIndex = i
                            break
                else:
                    useGame = False
            else:
                useGame = False

            if useGame and nGames[ratingIndex] >= gamesPerBand:
                useGame = False

            if onlyAnalysed and 'eval' not in line:
                useGame = False

            if useGame:
                game = chess.pgn.read_game(io.StringIO(currentPGN))
                nGames[ratingIndex] += 1

                with open(f'{outPath}{ratingBands[ratingIndex]}.pgn', 'a+') as f:
                    print(f'{currentPGN}\n\n', file=f)

            currentPGN = ""
            wElo = None
            bElo = None
            useGame = True
            ratingIndex = None


def extractMoves(pgnPaths: list) -> pl.DataFrame:
    keys = ['GameNr', 'Ply', 'WhiteElo', 'BlackElo', 'SideToMove', 'FEN', 'GamePhase', 'FromSquare', 'ToSquare', 'MovedPiece']
    data = dict()
    for key in keys:
        data[key] = list()

    gameNr = 0

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                wElo = game.headers["WhiteElo"]
                bElo = game.headers["BlackElo"]
                gameNr += 1
                ply = 0

                board = game.board()
                
                for move in game.mainline_moves():
                    data['GameNr'].append(gameNr)
                    data['Ply'].append(ply)
                    data['WhiteElo'].append(wElo)
                    data['BlackElo'].append(bElo)
                    data['SideToMove'].append(board.turn)
                    data['FEN'].append(board.fen())
                    data['GamePhase'].append(functions.getGamePhase(board))
                    data['FromSquare'].append(chess.square_name(move.from_square))
                    data['ToSquare'].append(chess.square_name(move.to_square))
                    data['MovedPiece'].append(board.piece_type_at(move.from_square))

                    ply += 1
                    board.push(move)
                    
    df = pl.DataFrame(data)
    return df


def getPieceMoveProbabilities(moveData: pl.DataFrame) -> dict:
    movedPieces = dict()
    for piece in [1, 2, 3, 4, 5, 6]:
        movedPieces[piece] = list()

    wPiece = None
    bPiece = None
    lastGameNr = 0
    for row in df.iter_rows(named=True):
        if row['GameNr'] != lastGameNr:
            wPiece = None
            bPiece = None
            lastGameNr = row['GameNr']

        position = row['FEN'].split(' ')[0]
        pieces = list()

        if row['SideToMove'] == chess.WHITE:
            for piece, i in [('P', chess.PAWN), ('N', chess.KNIGHT), ('B', chess.BISHOP), ('R', chess.ROOK), ('Q', chess.QUEEN), ('K', chess.KING)]:
                if piece in position:
                    pieces.append(i)

            movedPieces[row['MovedPiece']].append((wPiece, pieces))
            wPiece = row['MovedPiece']
        else:
            for piece, i in [('p', chess.PAWN), ('n', chess.KNIGHT), ('b', chess.BISHOP), ('r', chess.ROOK), ('q', chess.QUEEN), ('k', chess.KING)]:
                if piece in position:
                    pieces.append(i)

            movedPieces[row['MovedPiece']].append((bPiece, pieces))
            bPiece = row['MovedPiece']

    return movedPieces


def getFlankMoveProbabilities(moveData: pl.DataFrame) -> dict:
    data = dict()
    data['queenside'] = list()
    data['center'] = list()
    data['kingside'] = list()

    wSide = None
    bSide = None
    lastGameNr = 0
    for row in df.iter_rows(named=True):
        if row['GameNr'] != lastGameNr:
            wSide = None
            bSide = None
            lastGameNr = row['GameNr']
            continue

        if row['ToSquare'][0] in ['a', 'b', 'c']:
            side = 'queenside'
        elif row['ToSquare'][0] in ['d', 'e']:
            side = 'center'
        else:
            side = 'kingside'

        if row['SideToMove'] == chess.WHITE:
            data[side].append((wSide, bSide))
            wSide = side
        else:
            data[side].append((bSide, wSide))
            bSide = side

    return data


def getSamePieceMoveProbabilities(moveData: pl.DataFrame) -> dict:
    data = dict()
    for p in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        data[p] = [0, 0]

    wSquare = None
    bSquare = None
    lastGameNr = 0
    for row in df.iter_rows(named=True):
        if row['GameNr'] != lastGameNr:
            wSquare = None
            bSquare = None
            lastGameNr = row['GameNr']
            continue

        if wSquare is None and row['SideToMove'] == chess.WHITE:
            wSquare = row['ToSquare']
            continue
        if bSquare is None and row['SideToMove'] == chess.BLACK:
            bSquare = row['ToSquare']
            continue

        if row['SideToMove'] == chess.WHITE:
            lastSquare = wSquare
            wSquare = row['ToSquare']
            if bSquare == lastSquare:
                continue
        else:
            lastSquare = bSquare
            bSquare = row['ToSquare']
            if wSquare == lastSquare:
                continue
        
        if lastSquare == row['FromSquare']:
            data[row['MovedPiece']][0] += 1

        data[row['MovedPiece']][1] += 1

    return data


def plotPieceProbabilities(data: dict, filename: str = None):
    colors = plotting_helper.getDefaultColors()

    nBars = len(data)
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    legend = list(data.keys())

    pieces = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']
    xTicks = ['P', 'N', 'B', 'R', 'Q', 'K']
    fig, axs = plt.subplots(2, 3, figsize=(10, 6), sharey=True)

    for i in range(2):
        for j in range(3):
            axs[i][j].set_facecolor(plotting_helper.getColor('background'))

            plotData = [[data[rating][i*3 + j][k] for rating in data.keys()] for k in range(6)]
            print(plotData)

            for k in range(nBars):
                axs[i][j].bar([l+1+offset+(width*k) for l in range(len(plotData))], [d[k] for d in plotData], color=colors[k%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=legend[k])
                # axs[i][j].legend()
                axs[i][j].set_title(pieces[i*3 + j])
                axs[i][j].set_xticks([i+1 for i in range(6)], xTicks)

    fig.subplots_adjust(bottom=0.1, top=0.9, left=0.1, right=0.95)
    fig.suptitle('Piece move porbabilities', fontsize=17)
    # handles, labels = axs[0][0].get_legend_handles_labels()
    axs[1][1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=nBars)
    if filename:
        plt.savefig(filename, dpi=300)
    else:
        plt.show()


if __name__ == '__main__':
    ratingBands = [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]
    # extractGames(ratingBands, 10000, '180+0')
    """
    df = extractMoves(['../out/lichessDB/rating1200.pgn'])
    df.write_parquet('../out/lichessDBDF1200.par')
    df = extractMoves(['../out/lichessDB/rating1800.pgn'])
    df.write_parquet('../out/lichessDBDF1800.par')
    df = extractMoves(['../out/lichessDB/rating2200.pgn'])
    df.write_parquet('../out/lichessDBDF2200.par')
    df = extractMoves(['../out/lichessDB/rating2600.pgn'])
    df.write_parquet('../out/lichessDBDF2600.par')
    """

    df1200 = pl.read_parquet('../out/lichessDBDF1200.par')
    df1800 = pl.read_parquet('../out/lichessDBDF1800.par')
    df2200 = pl.read_parquet('../out/lichessDBDF2200.par')
    df2600 = pl.read_parquet('../out/lichessDBDF2600.par')

    ratings = [1200, 1800, 2200, 2600]
    pieceProbs = dict()

    sideProbs = dict()
    for side in ['queenside', 'center', 'kingside']:
        sideProbs[side] = [list() for _ in range(3)]
    baseSideProbs = [list() for _ in range(3)]

    samePieceProbs = [list() for _ in range(6)]

    baseProbs = list()
    for i, df in enumerate([df1200, df1800, df2200, df2600]):
        # df = df.filter((pl.col("Ply") >= 20) & (pl.col("Ply") <= 60))
        # df = df.filter(pl.col("Ply") <= 20)
        df = df.filter(pl.col("GamePhase") == "opening")

        """
        movedPieces = getPieceMoveProbabilities(df)
        baseProbs.append(list())
        print('Total probabilities:')
        for k, v in movedPieces.items():
            d = len(v)/sum([len([x for x in val if k in x[1]]) for val in movedPieces.values()])
            print(k, round(d, 3))
            baseProbs[-1].append(d)

        iProbs = list()
        print('Individual probabilities:')
        for k, v in movedPieces.items():
            probs = list()
            print(f'Moved piece: {k}')
            s = ""
            for p in [None, 1, 2, 3, 4, 5, 6]:
                if p:
                    d = len([val for val in v if val[0] == p]) / len([val for val in v if p in val[1]])
                else:
                    d = len([val for val in v if val[0] == p]) / len(v)
                s = f'{s}{p} {round(d, 3)}; '
                if p is not None:
                    probs.append(d)
            iProbs.append(probs)
            print(s)

        pieceProbs[ratings[i]] = iProbs
        """

        """
        sides = getFlankMoveProbabilities(df)
        print('Total:')
        for j, (k, v) in enumerate(sides.items()):
            d = len(v)/sum([len(x) for x in sides.values()])
            print(k, d)
            baseSideProbs[j].append(d)

        for j, (k, v) in enumerate(sides.items()):
            print(f'Current side: {k}')
            for l, s in enumerate(['queenside', 'center', 'kingside']):
                player = len([x for x in v if x[0] == s])/len(v)
                opponent = len([x for x in v if x[1] == s])/len(v)
                print(s, round(player, 3), round(opponent, 3))

                sideProbs[k][l].append((player, opponent))
        """

        samePiece = getSamePieceMoveProbabilities(df)
        print(ratings[i])
        for j, (k, v) in enumerate(samePiece.items()):
            print(k, v[0]/v[1])
            samePieceProbs[j].append(v[0]/v[1])

    # plotPieceProbabilities(pieceProbs)

    # print(sideProbs)
    # plotting_helper.plotPlayerBarChart(baseSideProbs, ['Queenside', 'Center', 'Kingside'], 'Relative number of moves', 'Move sides', ratings)
    """
    for side in ["queenside", "center", "kingside"]:
        for i, p in enumerate(['player', 'opponent']):
            plotData = [[v[i] for v in val] for val in sideProbs[side]]
            plotting_helper.plotPlayerBarChart(plotData, ['Queenside', 'Center', 'Kingside'], 'Relative number of moves', f'Move sides after {side} move by {p}', ratings)
    """

    """
    plotData = list()
    for i in range(6):
        plotData.append([v[i] for v in baseProbs])

    plotting_helper.plotPlayerBarChart(plotData, ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King'], 'Relative number of moves', 'How often pieces got moved', ['1200', '1800', '2200', '2600'])
    """

    plotting_helper.plotPlayerBarChart(samePieceProbs, ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King'], 'Relative number of moves', 'How often was the exact same piece moved twice', ['1200', '1800', '2200', '2600'])
