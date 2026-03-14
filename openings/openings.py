# Future Idea: calculate how much a player narrows the known moves
import os, sys
import subprocess
import chess
import re
import pickle
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper
import evalDB


def searchPositions(pgn: str, script: str, db: str) -> tuple:
    """
    Going through each game of a PGN and finding the novelties.
    pgn: str
        Path to the PGN file
    script: str
        Path to the SCID-script which looks if the position is new
    db: str
        Path to the SCID-database to compare the game to
    return -> tuple
        Tuple containing dictionaries with the novelties and book moves
    """
    # TODO: The output format of the TCL script has changed
    novelties = dict()
    # dictionary to count the book moves, values are lists with the number of moves with more than 10000, 1000, 100, 10, 1 games
    bookMoves = dict()
    cache = dict()
    gameNR = 1
    with open(pgn, 'r') as tournament:
        while (game := chess.pgn.read_game(tournament)):
            print(f'Starting with game {gameNR}')
            gameNR += 1

            white = game.headers["White"]
            black = game.headers["Black"]
            board = game.board()

            print(white, black)

            for move in game.mainline_moves():
                posBefore = board.fen()
                board.push(move)
                posAfter = board.fen()
                
                if posAfter in cache.keys():
                    numGames = cache[posAfter]
                else:
                    search = str(subprocess.run(['tkscid', script, db, posAfter], stdout=subprocess.PIPE).stdout)
                    numGames = gamesFromSearchOutput(search)
                    cache[posAfter] = numGames

                if board.turn:
                    player = black
                else:
                    player = white
                if numGames > 1:
                    if player not in bookMoves.keys():
                        bookMoves[player] = [0, 0, 0, 0, 0]
                    if numGames > 10000:
                        start = 0
                    elif numGames > 1000:
                        start = 1
                    elif numGames > 100:
                        start = 2
                    elif numGames > 10:
                        start = 3
                    else:
                        start = 4
                    for i in range(start, len(bookMoves[player])):
                        bookMoves[player][i] += 1
                    continue

                if not isMistake(posBefore, posAfter):
                    if player not in novelties.keys():
                        novelties[player] = 1
                    else:
                        novelties[player] += 1
                    print(f'Novelty: {move}')
                else:
                    print(f'No Novelty: {move}')
                break
    return (novelties, bookMoves)


def numberOfGames(pgnPath: str, script: str, db: str) -> dict:
    """
    This calculates the number of games after each move by a player.
    pgn: str
        Path to the PGN file
    script: str
        Path to the SCID-script which looks if the position is new
    db: str
        Path to the SCID-database to compare the game to
    return -> dict
        Dictionary indexed by player names, containing a list for each game where the first index shows the color (white=0, black=1), containing a tuple with the number of games before and after the player move
        dict(name, list(list(list(tuple(nGamesBefore, nGamesAfter))))
    """
    bookMoves = dict()
    cache = dict()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]
            print(white, black)
            # The first index indicates the color of the player in the game
            whiteMoves = [0]
            blackMoves = [1]

            board = game.board()

            for move in game.mainline_moves():
                posBefore = board.fen()
                board.push(move)
                posAfter = board.fen()
                
                if posBefore in cache.keys():
                    nGamesBefore = cache[posBefore]
                else:
                    search = str(subprocess.run(['tkscid', script, db, posBefore], stdout=subprocess.PIPE).stdout)
                    nGamesBefore = gamesFromSearchOutput(search)
                    cache[posBefore] = nGamesBefore

                if posAfter in cache.keys():
                    nGamesAfter = cache[posAfter]
                else:
                    search = str(subprocess.run(['tkscid', script, db, posAfter], stdout=subprocess.PIPE).stdout)
                    nGamesAfter = gamesFromSearchOutput(search)
                    cache[posAfter] = nGamesAfter

                if board.turn:
                    blackMoves.append((nGamesBefore, nGamesAfter))
                else:
                    whiteMoves.append((nGamesBefore, nGamesAfter))

                if nGamesAfter <= 1:
                    break

            if white in bookMoves.keys():
                bookMoves[white].append(whiteMoves)
            else:
                bookMoves[white] = [whiteMoves]
            if black in bookMoves.keys():
                bookMoves[black].append(blackMoves)
            else:
                bookMoves[black] = [blackMoves]
    return bookMoves


def gamesFromSearchOutput(output: str) -> int:
    """
    This function takes the output from a SCID search and extracts the number of games
    output: str
        The unformatted output
    return -> int
        The number of games found
    """
    games = re.findall(r'\d+', output)[0]
    return int(games)


def getClockTimesByPlayer(pgnPath: str, minutes: bool = True, startTime: int = 5400) -> dict:
    """
    This function reads the times from a PGN file with time stamps
    minutes: bool
        If this is set, the time will be calculated in minutes
    return -> dict
        {playerName: [[colorIndex, whiteTimeGame1, blackTimeGame1], [Game2Data], ... ]}
        where colorIndex is 1 for white and 2 for black and indicates the color of the player
    """
    times = dict()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]

            # The first index indicates the color of the player
            if minutes:
                c = [[startTime/60], [startTime/60]]
            else:
                c = [[startTime], [startTime]]

            node = game
            while not node.is_end():
                node = node.variations[0]
                if node.clock() is None:
                    continue
                time = int(node.clock())
                if minutes:
                    time /= 60
                if not time:
                    break
                if not node.turn():
                    c[0].append(time)
                else:
                    c[1].append(time)
            
            if white in times.keys():
                times[white].append([1, c[0], c[1]])
            else:
                times[white] = [[1, c[0], c[1]]]
            if black in times.keys():
                times[black].append([2, c[0], c[1]])
            else:
                times[black] = [[2, c[0], c[1]]]
    return times


def isMistake(posBefore: str, posAfter: str, mistakeThreshold: int = 10) -> bool:
    """
    This function takes the expected score of a position before and after a move and determines if the move was a mistake
    posBefore: str
        FEN string of the position before the move
    posAfter: str
        FEN string of the position after the move
    mistakeThreshold: int
        Centipawn loss which counts as a mistake
    return -> bool:
        True if the move was a mistake, False otherwise
    """
    sf = functions.configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    time = 3
    # if evalDB.contains(posBefore):
    if False:
        cpBefore = int(evalDB.getEval(posBefore, False))
    else:
        info = sf.analyse(chess.Board(posBefore), chess.engine.Limit(time=time))
        cpBefore = info['score'].white().score()
        # TODO: enter positions into eval DB
    # if evalDB.contains(posAfter):
    if False:
        cpAfter = int(evalDB.getEval(posAfter, False))
    else:
        info = sf.analyse(chess.Board(posAfter), chess.engine.Limit(time=time))
        cpAfter = info['score'].white().score()
        # TODO: enter positions into eval DB
    sf.quit()
    return abs(functions.expectedScore(cpBefore)-functions.expectedScore(cpAfter)) > mistakeThreshold


def sortPlayers(d: dict, index: int) -> list:
    """
    This function takes a dictionary with a list as values and sorts the keys by the value at the index of the list
    """

    players = list()
    for i in range(len(d.keys())):
        maximum = -1
        for k, v in d.items():
            if k in players:
                continue
            if isinstance(v, int):
                curr = v
            else:
                curr = v[index]
            if curr > maximum:
                p = k
                maximum = curr
        players.append(p)
    return players


def plotNovelties(novelties: dict, short: dict = None, filename: str = None):
    """
    This function plots the number of novelties per player
    novelties: dict
        A dictionary index by the players and the number of novelties as values
    short: dict
        Short names for the players to replace them in the graph
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved
    """
    sort = sortPlayers(novelties, 0)
    labels = list()
    for i, player in enumerate(sort):
        p = player.split(',')[0]
        if short:
            if p in short.keys():
                p = short[p]
        labels.append(p)

    fig, ax = plt.subplots(figsize=(10,6))

    ax.set_facecolor('#e6f7f2')
    plt.xticks(rotation=90)
    plt.yticks(range(0,9))
    plt.xticks(ticks=range(1, len(sort)+1), labels=labels)

    ax.bar([i+1 for i in range(len(sort))], [ novelties[p] for p in sort], color='#689bf2', edgecolor='black', linewidth=0.5, width=0.5, label='Novelties')
    ax.legend()
    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.1, right=0.95)
    plt.title('Number of novelties')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotBookMoves(bookMoves: dict, short: dict = None, filename: str = None, nGames: int = 14):
    """
    This function plots the number of book moves per player
    bookMoves: dict
        A dictionary index by the players and the number of book moves as values
    short: dict
        Short names for the players to replace them in the graph
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved
    nGames: int
        The number of games per player
    """
    sort = sortPlayers(bookMoves, 4)
    labels = list()
    for i, player in enumerate(sort):
        # p = player.split(',')[0]
        p = player
        if short:
            if p in short.keys():
                p = short[p]
        labels.append(p)

    fig, ax = plt.subplots(figsize=(10,6))

    ax.set_facecolor('#e6f7f2')
    plt.xticks(rotation=90)
    plt.xticks(ticks=range(1, len(sort)+1), labels=labels)
    plt.yticks(range(12))
    plt.ylim(0, 11.5)

    plt.grid(axis='y')

    values = list(bookMoves.values())
    width = 1 / (2*len(values[0]))
    offset = -width*(len(values[0])-0.5)/2

    legendNames = ['>10,000 games', '>1,000 games', '>100 games', '>10 games', '>1 game']
    colors = ['#689bf2', '#7ed3b2', '#ff87ca', '#beadfa', '#f8a978']

    for i in range(len(values[0])):
        # zorder=3 to have the bars in front of the grid lines
        ax.bar([j+1+offset for j in range(len(sort))], [bookMoves[p][i]/nGames for p in sort], width=width, label=legendNames[i], color=colors[i], edgecolor='black', linewidth=0.5, zorder=3)
        offset += width

    ax.legend(loc='upper center', ncol=5)
    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.05, right=0.95)
    plt.title('Number of book moves')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotBookMoveReductions(bookMoveData: dict, players: list = None):
    if players is None:
        players = list(bookMoveData.keys())

    fig, ax = plt.subplots(figsize=(10, 6))
    gameNr = 0
    for player, data in bookMoveData.items():
        if player not in players:
            continue

        for game in data:
            gameNr += 1
            if game[0] == 0:
                color = 'White'
                lineColor = 'blue'
            else:
                color = 'Black'
                lineColor = 'black'

            plotData = [d[1] for d in game[1:]]
            ax.plot(range(len(plotData)), plotData, label=f'{player}, {color}, {gameNr}', color=lineColor)

    ax.legend()
    ax.set_yscale('log')
    plt.show()


def analyseTimeUsage(clockTimes: dict):
    for player, clock in clockTimes.items():
        print(player)
        for game in clock:
            print(game[0])
            print([(game[1][i]-game[1][i+1])/game[1][0] for i in range(len(game[1])-1)])
            print([(game[2][i]-game[2][i+1])/game[2][0] for i in range(len(game[2])-1)])


def getNumberOfGames(pgnPath: str, script: str, database: str):
    """
    This function gets the number of games after each move in every game
    """
    bookMoves = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            date = game.headers["Date"]
            bm = list()
            board = game.board()
            for move in game.mainline_moves():
                n = int(subprocess.run(['tkscid', script, database, board.fen(), date], stdout=subprocess.PIPE, text=True).stdout.strip())
                bm.append(n)
                if n == 0:
                    break
                board.push(move)
            print(bm)
            bookMoves.append(bm)
    return bookMoves


def getMoveStatistics(db: str, moveScript: str, positionFEN: str, startDate: str, endDate: str) -> dict:
    """
    This function runs a tkscid script to determine how often each move was played in a given position
    """
    moveData = dict()
    moveStats = subprocess.run(['tkscid', moveScript, db, positionFEN, endDate, startDate], stdout=subprocess.PIPE, text=True).stdout.strip()
    for line in moveStats.split('\n'):
        if line.strip()[0].isnumeric():
            splitLine = line.split(':')[1].split()
            moveData[splitLine[0]] = int(splitLine[1])
    return moveData


def getMovesYearByYear(positionFEN: str, db: str, script: str, startYear: int, endYear: int) -> dict:
    yearlyMoves = dict()
    for year in range(startYear, endYear+1):
        moveStats = getMoveStatistics(db, script, positionFEN, f"{year-1}.12.31", f"{year}.12.31")
        yearlyMoves[year] = moveStats
    return yearlyMoves


def plotMovesByYear(positionFEN: str, db: str, script: str, startYear: int, endYear: int, movesToPlot: list, title: str, legend: list = None, filename: str = None):
    yearlyData = getMovesYearByYear(positionFEN, db, script, startYear, endYear)
    plotData = dict()
    for move in movesToPlot:
        plotData[move] = list()

    for moveData in yearlyData.values():
        total = sum(moveData.values())
        for move in movesToPlot:
            if move in moveData:
                plotData[move].append(moveData[move]/total)
            else:
                plotData[move].append(0)

    xValues = [list(yearlyData.keys())] * len(movesToPlot)
    if legend is None:
        moveNr = positionFEN.split()[-1]
        if positionFEN.split()[1] == 'w':
            moveNr = f'{moveNr}.'
        else:
            moveNr = f'{moveNr}...'
        legend = [f'{moveNr}{move}' for move in movesToPlot]

    plotting_helper.plotLineChart(xValues, list(plotData.values()), 'Year', 'Relative number of games', title, legend, filename=filename)


def plotPositionFrequencies(positions: list, db: str, script: str, startYear: int, endYear: int, referencePos: str, title: str, legend: list, combinedPositions: list = None, filename: str = None):
    """
    This function plots how often each position in the positions list was played relative to a reference position.
    The idea is to be able to compare different variations of an opening
    combinedPoistions: list
        Multiple positions that should be counted together
        [[pos11, pos12, ...], [...]]
    """
    plotData = list()
    referenceTotals = [int(subprocess.run(['tkscid', script, db, referencePos, f"{year-1}.12.31", f"{year}.12.31"], stdout=subprocess.PIPE, text=True).stdout.strip()) for year in range(startYear, endYear+1)]
    for fen in positions:
        posData = list()
        for year in range(startYear, endYear+1):
            if referenceTotals[year-startYear] == 0:
                posData.append(0)
                continue
            freq = int(subprocess.run(['tkscid', script, db, fen, f"{year-1}.12.31", f"{year}.12.31"], stdout=subprocess.PIPE, text=True).stdout.strip())
            posData.append(freq/referenceTotals[year-startYear])
        plotData.append(posData)

    if combinedPositions is not None:
        for positions in combinedPositions:
            posData = list()
            for year in range(startYear, endYear+1):
                if referenceTotals[year-startYear] == 0:
                    posData.append(0)
                    continue
                total = 0
                for fen in positions:
                    freq = int(subprocess.run(['tkscid', script, db, fen, f"{year-1}.12.31", f"{year}.12.31"], stdout=subprocess.PIPE, text=True).stdout.strip())
                    total += freq
                posData.append(total/referenceTotals[year-startYear])
            plotData.append(posData)


    xValues = [list(range(startYear, endYear+1))] * len(plotData)
    plotting_helper.plotLineChart(xValues, plotData, 'Year', 'Relative number of games', title, legend, filename=filename)


if __name__ == '__main__':
    # db = '/home/julian/chess/database/gameDB/novelties'
    db = '/Users/julian/Desktop/gameDB/chessDB'
    db = '/Users/julian/Library/Mobile Documents/com~apple~CloudDocs/chessDB'
    classicalDB = '/Users/julian/Library/Mobile Documents/com~apple~CloudDocs/classicalGames'
    player = 'Carlsen, M.'
    script = 'searchPosition.tcl'
    pgn = '../out/candidates2024-WDL+CP.pgn'
    usChamps = '../resources/usChamps2025.pgn'
    fen = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'
    moveScript = 'getMoveFrequencies.tcl'
    e4Pos = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1'
    sicilian = 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2'
    preNajdorf = 'rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R b KQkq - 2 5'
    # Sicilian variations
    najdorf = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'
    classicalSicilian = 'r1bqkb1r/pp2pppp/2np1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 3 6'
    dragon = 'rnbqkb1r/pp2pp1p/3p1np1/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'
    sveshnikov = 'r1bqkb1r/pp1p1ppp/2n2n2/4p3/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'
    kalashnikov = 'r1bqkbnr/pp3ppp/2np4/1N2p3/4P3/8/PPP2PPP/RNBQKB1R w KQkq - 0 6'
    lowenthal = 'r1bqkbnr/1p1p1ppp/p1n5/1N2p3/4P3/8/PPP2PPP/RNBQKB1R w KQkq - 0 6'
    taimanov = 'r1bqkbnr/pp1p1ppp/2n1p3/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 1 5'
    kan = 'rnbqkbnr/1p1p1ppp/p3p3/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 5'
    accDragon = ['rnbqkbnr/pp1ppp1p/6p1/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3', 'rnbqkbnr/pp2pp1p/3p2p1/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 5']

    # Bg5 Najdorf variations
    Bg5Start = 'rnbqkb1r/1p2pppp/p2p1n2/6B1/3NP3/2N5/PPP2PPP/R2QKB1R b KQkq - 1 6'
    poisonedPawn = 'rnb1kb1r/1p3ppp/pq1ppn2/6B1/3NPP2/2N5/PPP3PP/R2QKB1R w KQkq - 1 8'
    e6f4Be7 = 'rnbqk2r/1p2bppp/p2ppn2/6B1/3NPP2/2N5/PPP3PP/R2QKB1R w KQkq - 1 8'
    Nbd7 = 'r1bqkb1r/1p1npppp/p2p1n2/6B1/3NP3/2N5/PPP2PPP/R2QKB1R w KQkq - 2 7'
    e6f4h6 = 'rnbqkb1r/1p3pp1/p2ppn1p/6B1/3NPP2/2N5/PPP3PP/R2QKB1R w KQkq - 0 8'
    e6f4Nbd7 = 'r1bqkb1r/1p1n1ppp/p2ppn2/6B1/3NPP2/2N5/PPP3PP/R2QKB1R w KQkq - 1 8'
    e6f4Qc7 = 'rnb1kb1r/1pq2ppp/p2ppn2/6B1/3NPP2/2N5/PPP3PP/R2QKB1R w KQkq - 1 8'

    # move 2 alternatives for White
    closedSicilian = 'rnbqkbnr/pp1ppppp/8/2p5/4P3/2N5/PPPP1PPP/R1BQKBNR b KQkq - 1 2'
    alapin = 'rnbqkbnr/pp1ppppp/8/2p5/4P3/2P5/PP1P1PPP/RNBQKBNR b KQkq - 0 2'
    smithMorra = 'rnbqkbnr/pp1ppppp/8/2p5/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2'
    openSicilians = ['rnbqkbnr/pp2pppp/3p4/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3', 'r1bqkbnr/pp1ppppp/2n5/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3', 'rnbqkbnr/pp1p1ppp/4p3/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3', 'rnbqkbnr/pp1ppp1p/6p1/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3']
    delayedAlapin = ['r1bqkbnr/pp1ppppp/2n5/2p5/4P3/2P2N2/PP1P1PPP/RNBQKB1R b KQkq - 0 3', 'rnbqkbnr/pp2pppp/3p4/2p5/4P3/2P2N2/PP1P1PPP/RNBQKB1R b KQkq - 0 3', alapin]
    moscow = 'rnbqkbnr/pp2pppp/3p4/1Bp5/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 1 3'
    rossolimo = 'r1bqkbnr/pp1ppppp/2n5/1Bp5/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3'

    e4c5Nf3 = 'rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2'
    # getMovesYearByYear(e4Pos, classicalDB, moveScript, 1900, 2000)
    # plotMovesByYear(e4Pos, classicalDB, moveScript, 1850, 2026, ['e5', 'c5', 'e6', 'c6', 'd6', 'g6', 'd5', 'Nf6'], 'Relative number of games with different responses to 1.e4', filename='../out/openingFreqPlots/e4.png')
    # plotMovesByYear(preNajdorf, classicalDB, moveScript, 1900, 2026, ['a6', 'Nc6', 'g6', 'e6'])
    plotMovesByYear(najdorf, classicalDB, moveScript, 1950, 2026, ['Be3', 'Bg5', 'Bc4', 'h3', 'f3', 'Rg1', 'Be2', 'Bd3', 'g3', 'f4'], 'Popularity of different 6th moves for white in the Najdorf variation' , filename='../out/openingFreqPlots/najdorf.png')
    # plotMovesByYear(e4c5Nf3, classicalDB, moveScript, 1850, 2026, ['d6', 'Nc6', 'e6', 'g6', 'Nf6', 'a6', 'Qc7'])

    # plotPositionFrequencies([najdorf, classicalSicilian, dragon, sveshnikov, kalashnikov, taimanov, kan], classicalDB, script, 1920, 2026, e4c5Nf3, 'Relative number of games in different open Sicilian variations', ['Naidorf Variation', 'Classical Sicilian', 'Dragon Variation', 'Sveshnikov Variation', 'Kalashnikov Variation', 'Taimanov Variation', 'Kan Variation', '(Hyper-)accelerated Dragon'], combinedPositions=[accDragon], filename='../out/openingFreqPlots/openSicilians.png')
    # plotPositionFrequencies([closedSicilian, smithMorra, moscow, rossolimo], classicalDB, script, 1920, 2026, sicilian,  'Relative number of games after 1.e4 c5 with different Sicilian variations', ['Closed Sicilian', 'Smith-Morra Gambit', 'Moscow Variation', 'Rossolimo Variation', 'Open Sicilian', 'Alapin Variation'], combinedPositions=[openSicilians, delayedAlapin], filename='../out/openingFreqPlots/e4c5.png')
    # plotPositionFrequencies([poisonedPawn, e6f4Be7, Nbd7, e6f4h6, e6f4Nbd7, e6f4Qc7], classicalDB, script, 1950, 2026, Bg5Start, 'Bg5 Najdorf', ['Poisoned pawn', '6...e6 7.f4 Be7', '6...Nbd7', '6...e6 7.f4 h6', '6...e6 7.f4 Nbd7', '6...e6 7.f4 Qc7'])

    # print(getNumberOfGames('../resources/vanForeest-gukesh.pgn', script, db))
    
    # numGames = numberOfGames(usChamps, script, db)
    # with open('../out/usChampsBook.pkl', 'wb+') as f:
    #     pickle.dump(numGames, f)

    # with open('../out/usChampsBook.pkl', 'rb+') as f:
        # numGames = pickle.load(f)
    # print(numGames)
    # print(getClockTimesByPlayer(usChamps))
    # plotBookMoveReductions(numGames, ['Sevian, Samuel'])

    # print(o)
    # print(gamesFromSearchOutput(str(o)))

    # arjunC = '../out/arjun_closed.pgn'
    # arjunO = '../out/arjun_open-5000-30.pgn'

    # clockTimes = getClockTimesByPlayer('../resources/ding-gukesh-clocks.pgn', startTime=7200)
    # analyseTimeUsage(clockTimes)
    """
    novC, bookC = searchPositions(arjunC, script, db)
    plotNovelties(novC)
    plotBookMoves(bookC)

    with open(f'../out/arjun_closed-novelties.pkl', 'wb+') as f:
        pickle.dump(novC, f)
    with open(f'../out/arjun_closed-bookMoves.pkl', 'wb+') as f:
        pickle.dump(bookC, f)
    novO, bookO = searchPositions(arjunO, script, db)
    plotNovelties(novO)
    plotBookMoves(bookO)
    with open(f'../out/arjun_open-novelties.pkl', 'wb+') as f:
        pickle.dump(novO, f)
    with open(f'../out/arjun_open-bookMoves.pkl', 'wb+') as f:
        pickle.dump(bookO, f)
    """

    """
    with open(f'../out/arjun_closed-bookMoves.pkl', 'rb') as f:
        arjun_closed = pickle.load(f)
    with open(f'../out/arjun_open-bookMoves.pkl', 'rb') as f:
        arjun_open = pickle.load(f)

    name = 'Erigaisi, Arjun'
    moves = {f'{name}\nClosed': arjun_closed[name], f'{name}\nOpen': [x*32 / 37 for x in arjun_open[name]]}
    plotBookMoves(moves, filename='../out/arjunBookMoves.png', nGames=32)
    """

    """
    nov, book = searchPositions(pgn, script, db)
    print(nov, book)
    with open(f'../out/candidates-novelties.pkl', 'wb+') as f:
        pickle.dump(nov, f)
    with open(f'../out/candidates-bookMoves.pkl', 'wb+') as f:
        pickle.dump(book, f)
    """
    """
    with open(f'../out/candidates-novelties.pkl', 'rb+') as f:
        novelties = pickle.load(f)
    nicknames = {'Nepomniachtchi': 'Nepo', 'Praggnanandhaa R': 'Pragg'}
    with open(f'../out/candidates-bookMoves.pkl', 'rb+') as f:
        bookMoves = pickle.load(f)
    """
    # plotNovelties(novelties, short=nicknames, filename='../out/novelties.png')
    # plotBookMoves(bookMoves, short=nicknames, filename='../out/bookMoves.png')
