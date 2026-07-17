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


def extractMoves(pgnPaths: list, startTime: int) -> pl.DataFrame:
    keys = ['GameNr', 'Ply', 'WhiteElo', 'BlackElo', 'SideToMove', 'FEN', 'GamePhase', 'FromSquare', 'ToSquare', 'MovedPiece', 'TimeLeft']
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
                wTime = startTime
                bTime = startTime

                board = game.board()
                node = game

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
                    if node.turn():
                        data['TimeLeft'].append(wTime)
                    else:
                        data['TimeLeft'].append(bTime)

                    ply += 1
                    board.push(move)
                    node = node.variations[0]
                    
                    if node.clock() is not None:
                        if node.turn():
                            bTime = int(node.clock())
                        else:
                            wTime = int(node.clock())

    df = pl.DataFrame(data)
    return df


def getPieceMoveProbabilities(moveData: pl.DataFrame) -> dict:
    """
    This gets the moved pieces from the move-by-move data
    return -> dict:
        {1: [(movedPieceBeforePawn1, piecesOnTheBoard1), (movedPieceBeforePawn2, piecesOnTheBoard2), ...], 2: ...}
    """
    movedPieces = dict()
    for piece in [1, 2, 3, 4, 5, 6]:
        movedPieces[piece] = list()

    wPiece = None
    bPiece = None
    lastGameNr = 0
    for row in moveData.iter_rows(named=True):
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
    for row in moveData.iter_rows(named=True):
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
    for row in moveData.iter_rows(named=True):
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


def plotPieceProbabilities(data: dict, title: str, colors: list = None, filename: str = None):
    if colors is None:
        colors = plotting_helper.getDefaultColors()

    nBars = len(data)
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    legend = list(data.keys())

    pieces = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']
    xTicks = ['P', 'N', 'B', 'R', 'Q', 'K']
    fig, axs = plt.subplots(2, 3, figsize=(12, 6), sharex=True, sharey=True)

    for i in range(2):
        for j in range(3):
            axs[i][j].set_facecolor(plotting_helper.getColor('background'))

            plotData = [[data[rating][i*3 + j][k] for rating in data.keys()] for k in range(6)]

            for k in range(nBars):
                axs[i][j].bar([l+1+offset+(width*k) for l in range(len(plotData))], [d[k] for d in plotData], color=colors[k%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=legend[k])
                # axs[i][j].legend()
                axs[i][j].set_title(f'After a {pieces[i*3 + j]} move')
                axs[i][j].set_xticks([i+1 for i in range(6)], xTicks)

    fig.subplots_adjust(bottom=0.15, top=0.9, left=0.07, right=0.97)
    fig.suptitle(title, fontsize=15)
    axs[1][1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=nBars)
    axs[1][1].set_xlabel("Moved piece")
    fig.text(0.02, 0.5, "Relative number of moves", va="center", rotation="vertical")

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotSideProbabilities(data: dict, title: str, ratings: list, colors: list = None, filename: str = None):
    if colors is None:
        colors = plotting_helper.getDefaultColors()

    nBars = len(ratings)
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    xTicks = ['Queenside', 'Center', 'Kingside']
    fig, axs = plt.subplots(2, 3, figsize=(12, 6), sharex=True, sharey=True)

    for i, p in enumerate(['same player', 'opponent']):
        for j, side in enumerate(['queenside', 'center', 'kingside']):
            axs[i][j].set_facecolor(plotting_helper.getColor('background'))

            plotData = [[d[i] for d in data[side][k]] for k in range(3)]

            for k in range(nBars):
                axs[i][j].bar([l+1+offset+(width*k) for l in range(len(plotData))], [d[k] for d in plotData], color=colors[k%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=ratings[k])
                # axs[i][j].legend()
                axs[i][j].set_title(f'After a {side} move by the {p}')
                axs[i][j].set_xticks([i+1 for i in range(len(xTicks))], xTicks)

    fig.subplots_adjust(bottom=0.15, top=0.9, left=0.07, right=0.97)
    fig.suptitle(title, fontsize=15)
    axs[1][1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=nBars)
    axs[1][1].set_xlabel("Side of the board of the move played")
    fig.text(0.02, 0.5, "Relative number of moves", va="center", rotation="vertical")

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def generatePlots(dfs: list, ratings: list, gamePhases: list, colors: list = None, outpath: str = None):
    for gamePhase in gamePhases:
        pieceProbs = dict()

        sideProbs = dict()
        for side in ['queenside', 'center', 'kingside']:
            sideProbs[side] = [list() for _ in range(3)]
        baseSideProbs = [list() for _ in range(3)]

        samePieceProbs = [list() for _ in range(6)]

        baseProbs = list()
        for i, df in enumerate(dfs):
            df = df.filter(pl.col("GamePhase") == gamePhase)
            df = df.filter(pl.col("TimeLeft") > 30)

            movedPieces = getPieceMoveProbabilities(df)
            baseProbs.append(list())
            for k, v in movedPieces.items():
                d = len(v)/sum([len([x for x in val if k in x[1]]) for val in movedPieces.values()])
                baseProbs[-1].append(d)

            iProbs = list()
            for k, v in movedPieces.items():
                probs = list()
                baseNumber = len([v for index in range(6) for v in list(movedPieces.values())[index] if v[0] == k])
                for p in [None, 1, 2, 3, 4, 5, 6]:
                    if p:
                        # d = len([val for val in v if val[0] == p]) / len([val for val in v if p in val[1]])
                        # baseNumber = len([v for index in range(6) for v in list(movedPieces.values())[index] if v[0] == p])
                        # d = len([val for val in v if val[0] == p]) / baseNumber
                        n = len([v for v in movedPieces[p] if v[0] == k])
                        d = n / baseNumber
                    else:
                        d = len([val for val in v if val[0] == p]) / len(v)
                    if p is not None:
                        probs.append(d)
                iProbs.append(probs)

            pieceProbs[ratings[i]] = iProbs

            sides = getFlankMoveProbabilities(df)
            for j, (k, v) in enumerate(sides.items()):
                d = len(v)/sum([len(x) for x in sides.values()])
                baseSideProbs[j].append(d)

            for j, (k, v) in enumerate(sides.items()):
                sidesBaseNumberPlayer = len([x for index in range(3) for x in list(sides.values())[index] if x[0] == k])
                sidesBaseNumberOpponent = len([x for index in range(3) for x in list(sides.values())[index] if x[1] == k])
                for l, s in enumerate(['queenside', 'center', 'kingside']):
                    # player = len([x for x in v if x[0] == s])/len(v)
                    # opponent = len([x for x in v if x[1] == s])/len(v)

                    player = len([x for x in sides[s] if x[0] == k]) / sidesBaseNumberPlayer
                    opponent = len([x for x in sides[s] if x[1] == k]) / sidesBaseNumberOpponent

                    sideProbs[k][l].append((player, opponent))

            samePiece = getSamePieceMoveProbabilities(df)
            totalMoves = sum([v[1] for v in samePiece.values()])
            for j, (k, v) in enumerate(samePiece.items()):
                # samePieceProbs[j].append(v[0]/v[1])
                samePieceProbs[j].append(v[0]/totalMoves)

        if outpath is None:
            filenames = [None] * 5
        else:
            endings = [f'baslinePieces-{gamePhase}.png', f'pieceProbs-{gamePhase}.png', f'baselineSides-{gamePhase}.png', f'sides-{gamePhase}.png', f'samePiece-{gamePhase}.png']
            filenames = [f'{outpath}{ending}' for ending in endings]

        plotData = list()
        for i in range(6):
            plotData.append([v[i] for v in baseProbs])

        plotting_helper.plotPlayerBarChart(plotData, ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King'], 'Relative number of moves', f'Relative number of moves with each piece in the {gamePhase}', ratings, colors=colors, filename=filenames[0])

        plotPieceProbabilities(pieceProbs, title=f'Piece move porbabilities in the {gamePhase} after each piece was moved', colors=colors, filename=filenames[1])

        plotting_helper.plotPlayerBarChart(baseSideProbs, ['Queenside', 'Center', 'Kingside'], 'Relative number of moves', f'Realtive number of moves on each side of the board in the {gamePhase}', ratings, colors=colors, legendUnderPlot=True, filename=filenames[2])

        plotSideProbabilities(sideProbs, f'Relative number of moves on each side of the board, depending on the side of the last move in the {gamePhase}', ratings, colors=colors, filename=filenames[3])
        """
        for side in ["queenside", "center", "kingside"]:
            for i, p in enumerate(['same player', 'opponent']):
                if filenames[3] is None:
                    filename = None
                else:
                    filename = f'{filenames[3]}-{side}-{p.split()[-1]}.png'
                plotData = [[v[i] for v in val] for val in sideProbs[side]]
                plotting_helper.plotPlayerBarChart(plotData, ['Queenside', 'Center', 'Kingside'], 'Relative number of moves', f'Relative number of moves on each board side after a {side} move by the {p} in the {gamePhase}', ratings, colors=colors, filename=filename)
        """

        plotting_helper.plotPlayerBarChart(samePieceProbs, ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King'], 'Relative number of moves', f'Relative number of moves that the exact same piece got moved twice in a row in the {gamePhase}', ratings, colors=colors, filename=filenames[4])


if __name__ == '__main__':
    ratingBands = [1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]
    ratingBands = [1000, 1400, 1800, 2200, 2600]
    # extractGames(ratingBands, 20000, '180+0', maxRatingDiff=75, outPath='../out/lichessDB/blitz_3+0_')
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


    ratings = [1000, 1400, 1800, 2200, 2600]
    dfs = list()
    for rating in ratings:
        # pgnPath = f'../out/lichessDB/blitz_3+0_{rating}.pgn'
        # df = extractMoves([pgnPath], startTime=180)
        parPath = f'../out/lichessDBDF_blitz_{rating}.par'
        # df.write_parquet(outPath)
        df = pl.read_parquet(parPath)
        dfs.append(df)
    
    colors = plotting_helper.getColors(["red", "orange", "green", "blue", "purple"])
    generatePlots(dfs, ratings, ["opening", "middlegame"], colors=colors, outpath='../out/moveProbabilities/')
    # generatePlots(dfs, ratings, ["opening"], colors=colors)

    # df1200 = pl.read_parquet('../out/lichessDBDF1200.par')
    # df1800 = pl.read_parquet('../out/lichessDBDF1800.par')
    # df2200 = pl.read_parquet('../out/lichessDBDF2200.par')
    # df2600 = pl.read_parquet('../out/lichessDBDF2600.par')

    ratings = [1200, 1800, 2200, 2600]

    # generatePlots([df1200, df1800, df2200, df2600], ratings, ["opening"])# , "middlegame"])

