import chess
import chess.pgn
import subprocess

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper

import matplotlib.pyplot as plt
import time
import pickle
import numpy as np


def getPlayerTimes(game: chess.pgn.Game, startTime: int = 5430, increment: int = 30) -> list:
    """
    This function extracts the clock times for each player from a chess.Game object
    startTime: int
        The time at the start of the game in seconds
    return -> list
        [[wTimeBeforeMove1, wTimeBeforeMove2, ...], [bTimeBeforeMove1, ...]]
    """
    wTime = [startTime]
    bTime = [startTime]

    node = game
    while not node.is_end():
        node = node.variations[0]

        if not node.turn():
            if node.clock() is None:
                time = wTime[-1] + increment # if no time is given, I assume that the move was played instantly
            else:
                time = int(node.clock())

            wTime.append(time)
        else:
            if node.clock() is None:
                time = bTime[-1] + increment
            else:
                time = int(node.clock())
            bTime.append(time)
    return [wTime, bTime]


def getNumberOfGamesBeforeEachMove(game: chess.pgn.Game, script: str, db: str) -> list:
    """
    This function gets the number of games in the database before each move in the game
    game: chess.Game
        The given game
    script: str
        Path to the tkscid script to get the number of games in the database
    db: str
        Path to the SCID database
    return -> list
        [nGamesBeforeMove1, nGamesBeforeMove2, ...]
    """
    nGames = list()

    board = game.board()
    date = game.headers["Date"]
    for move in game.mainline_moves():
        n = int(subprocess.run(['tkscid', script, db, board.fen(), date], stdout=subprocess.PIPE, text=True).stdout.strip())
        nGames.append(n)
        if n == 0:
            break
        board.push(move)

    return nGames


def getFirstThinks(clockTimes: list) -> list:
    """
    This function looks at the clock times and returns the moves where the players first started to think
    return -> list:
        [[wThinkIndex1, ...], [bThinkIndex1, ...]]
        If a player thinks and then plays instantly again, multiple think indices will be given
    """
    instantMoveThreshold = 90
    mediumThinkThreshold = 300

    thinkIndices = list()
    for playerTime in clockTimes:
        thinks = list()
        instantMove = True

        for i in range(len(playerTime)-1):
            timeSpent = playerTime[i] - playerTime[i+1]
            if timeSpent > instantMoveThreshold and not instantMove:
                break
            if timeSpent < instantMoveThreshold:
                instantMove = True
            elif timeSpent < mediumThinkThreshold:
                thinks.append(i)
                instantMove = False
            else:
                thinks.append(i)
                break
        thinkIndices.append(thinks)
    return thinkIndices


def getMoveStatistics(db: str, moveScript: str, positionFEN: str, date: str) -> dict:
    """
    This function runs a tkscid script to determine how often each move was played in a given position
    """
    moveData = dict()
    moveStats = subprocess.run(['tkscid', moveScript, db, positionFEN, date], stdout=subprocess.PIPE, text=True).stdout.strip()
    for line in moveStats.split('\n'):
        if line.strip()[0].isnumeric():
            splitLine = line.split(':')[1].split()
            moveData[splitLine[0]] = splitLine[1]
    return moveData


def getBookMoves(pgnPath: str, script: str, db: str, startTime: int = 5430, increment: int = 30):
    """
    """
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            clockTimes = getPlayerTimes(game, startTime, increment)
            # nGames = getNumberOfGamesBeforeEachMove(game, script, db)
            nGames = None
            gameDate = game.headers["Date"]

            print(clockTimes)
            firstThinkIndices = getFirstThinks(clockTimes)
            wTime = clockTimes[0]
            bTime = clockTimes[1]

            moveIndices = list()

            for i, thinks in enumerate(firstThinkIndices):
                for t in thinks:
                    if i == 0:
                        moveIndices.append(t*2-1)
                    else:
                        moveIndices.append(t*2)
                    
                if len(thinks) == 1:
                    continue


                if i == 0:
                    thinkTime = wTime[thinks[0]] - wTime[thinks[0]+1]
                    oppThinkTime = bTime[thinks[0]-1] - bTime[thinks[0]]
                else:
                    thinkTime = bTime[thinks[0]] - bTime[thinks[0]+1]
                    oppThinkTime = wTime[thinks[0]] - wTime[thinks[0]+1]

            print(thinkTime, oppThinkTime)
            print(firstThinkIndices)
            print(len(clockTimes[0]), len(clockTimes[1]))
            print(moveIndices)

            board = game.board()
            moveNr = 0
            for move in game.mainline_moves():
                if moveNr in moveIndices:
                    print(board)
                    print(getMoveStatistics(db, script, board.fen(), gameDate))
                board.push(move)
                moveNr += 1


def plotTimeSpentPerPlayer(pgnPath: str, maxMove: int = None):
    times = dict()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            colorTimes = getPlayerTimes(game)
            white = game.headers["White"]
            black = game.headers["Black"]

            if white in times:
                times[white].append(colorTimes[0])
            else:
                times[white] = [colorTimes[0]]

            if black in times:
                times[black].append(colorTimes[1])
            else:
                times[black] = [colorTimes[1]]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor(plotting_helper.getColor('background'))

    colors = plotting_helper.getDefaultColors()

    colorIndex = 0
    for player, t in times.items():
        for i, yValues in enumerate(t):
            if maxMove is not None:
                yValues = yValues[:maxMove]
            if i == 0:
                ax.plot(list(range(1, len(yValues)+1)), yValues, color=colors[colorIndex], label=player)
            else:
                ax.plot(list(range(1, len(yValues)+1)), yValues, color=colors[colorIndex])
        colorIndex += 1
    
    ax.legend()
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.show()


def getBookMovesPerYear(pgnPaths: list, scriptPath: str, dbPath: str) -> dict:
    """
    This gets the book moves every year in the given PGN file
    pgnPaths: list
        Paths to the PGN files one wants to analyse
    scriptPath: str
        Path to the TCL script that gets the number of games in the database
    dbPath: str
        Path to the SCID database, which is the reference for the number of games
    return -> dict:
        {year: [bookPlyGame1, bookPlyGame2, ...], ...}
    """
    games = list()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                date = game.headers["Date"].replace('??', '00')

                games.append((date, game))

    games = sorted(games, key=lambda x:x[0])

    bookPly = dict()

    cache = list()
    cacheBuffer = list()
    lastDate = None
    gameNr = 0

    proc = subprocess.Popen(['tkscid', script, db], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    for date, game in games:
        # print(gameNr, date)
        # gameNr += 1
        # gameStartTime = time.time()

        """
        if 'WhiteElo' not in game.headers or 'BlackElo' not in game.headers:
            with open('../out/bookMovesLogRatings.txt', 'a+') as f:
                f.write(f'{game.headers["White"]}-{game.headers["Black"]}, {date}\n')
        """

        if lastDate is None:
            lastDate = date

        if date != lastDate:
            cache.extend(cacheBuffer)
            cacheBuffer = list()
            lastDate = date
        
        if (year := int(date.split('.')[0])) not in bookPly:
            bookPly[year] = list()

        searchDate = date
        spDate = searchDate.split('.')
        if spDate[2] == '00':
            if spDate[1] == '00':
                searchDate = f'{int(spDate[0])-1}.12.31'
            else:
                searchDate = f'{spDate[0]}.{int(spDate[1])-1}.31'
        else:
            searchDate = f'{spDate[0]}.{spDate[1]}.{int(spDate[2])-1}'

        board = game.board()
        ply = 0
        fenBuffer = list()
        for move in game.mainline_moves():
            board.push(move)
            ply += 1

            fen = board.fen()
            if fen in cache:
                continue

            fenBuffer.append(fen)
            if len(fenBuffer) < 5:
                continue

            proc.stdin.write(f'{fen}\t{searchDate}\n')
            proc.stdin.flush()
            nGames = int(proc.stdout.readline())

            i = 0
            if nGames > 0:
                # cacheBuffer.extend(fenBuffer)
                cacheBuffer.append(fen)
                fenBuffer = list()
            else:
                for i, f in enumerate(fenBuffer):
                    if f in cache:
                        continue

                    proc.stdin.write(f'{f}\t{searchDate}\n')
                    proc.stdin.flush()
                    nGames = int(proc.stdout.readline())
                    if nGames == 0:
                        bookPly[year].append(ply-(len(fenBuffer)-i)+1)
                        break
                    else:
                        cacheBuffer.append(f)
                break

        # print(round(time.time()-gameStartTime, 2), ply-len(fenBuffer)+i+1)
        """
        if ply-len(fenBuffer)+i+1 >= 50:
            with open('../out/bookMovesLog.txt', 'a+') as f:
                f.write(f'{game.headers["White"]}-{game.headers["Black"]}, {date}, {ply-len(fenBuffer)+i+1}\n')
        """

    return bookPly


def analyseOpeningData(data: dict):
    for year, moveNrs in data.items():
        print(f'{year}: min={min(moveNrs)}\tq1={round(np.quantile(moveNrs, 0.25), 2)}\tq2={round(np.quantile(moveNrs, 0.5), 2)}\tq3={round(np.quantile(moveNrs, 0.75), 2)}\tmax={max(moveNrs)}')


def plotOpeningData(dataPaths: list, title: str, filename: str = None):
    rawData = dict()
    for path in dataPaths:
        data = pickle.load(open(path, 'rb'))
        for k, v in data.items():
            if max(v) > 80:
                v.remove(max(v))
            if k not in rawData:
                rawData[k] = v
            else:
                rawData[k].extend(v)

    rawData = dict(sorted(rawData.items())[:-1])

    plotData = list()
    plotData.append([(sum(v)/len(v))/2 if len(v) > 0 else 0 for v in rawData.values()])
    percentiles = [0.25, 0.5, 0.75]
    percentiles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    percentiles = [0.2, 0.4, 0.6, 0.8]
    legend = ['Average']
    legend.extend([f'{int(p*100)}th percentile' for p in percentiles])
    for p in percentiles:
        plotData.append([np.quantile(v, p)/2 for v in rawData.values()])

    plotting_helper.plotLineChartSingleX(plotData, 'Year', 'Number of moves', title, legend, xTicks=list(rawData.keys()), colors=plotting_helper.getColors(['green', 'red', 'orange', 'blue', 'purple']), filename=filename)
    # plotting_helper.plotBoxplot(list(rawData.values()), 'Year', 'Number of moves', title)


def plotDifferentPlayerGroups(dataPaths: list, title: str, legend: list, filename: str = None):
    rawData = dict()
    for i, paths in enumerate(dataPaths):
        for path in paths:
            data = pickle.load(open(path, 'rb'))
            for k, v in data.items():
                if max(v) > 80:
                    v.remove(max(v))

                if k not in rawData:
                    rawData[k] = [v]
                elif len(rawData[k]) == i+1:
                    rawData[k][-1].extend(v)
                else:
                    rawData[k].append(v)

    rawData = dict(sorted(rawData.items())[:-1])
    plotData = [[(sum(v[i])/len(v[i]))/2 if len(v) > 0 else 0 for v in rawData.values()] for i in range(len(dataPaths))]

    plotting_helper.plotLineChartSingleX(plotData, 'Year', 'Number of moves', title, legend, xTicks=list(rawData.keys()), filename=filename)


if __name__ == '__main__':
    db = '/Users/julian/Library/Mobile Documents/com~apple~CloudDocs/chessDB'
    db = '/Users/julian/Desktop/classicalDB2'
    db = '/home/julian/chess/database/gameDB/classicalDB'
    script = 'searchPosition.tcl'
    script = 'searchPositionFast.tcl'
    pgn = '../resources/vanForeest-gukesh.pgn'
    moveScript = 'getMoveFrequencies.tcl'
    # getBookMoves(pgn, moveScript, db)
    najdorf = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'
    # print(getMoveStatistics(db, moveScript, najdorf, '2025.01.01'))
    # plotTimeSpentPerPlayer(prague, 40)

    pgn = '../resources/2500+gamesUTF8.pgn'
    pgn = '../resources/carlsenGames.pgn'
    pgn = '../resources/2650gamesSince2000UTF8.pgn'
    # pgn = '../out/carlsen-caruana-g1-WDL10000.pgn'
    # pgn = '../resources/candidates2024.pgn'
    pgn = '../resources/2650gamesClassical2023.pgn'
    pgn = '../resources/2600games1980-2000.pgn'
    pgns = ['../resources/matches/lasker-schlechter1910.pgn', '../resources/tournaments/hamburg1910.pgn', '../resources/tournaments/sanSebastian1911.pgn', '../resources/tournaments/newYork1911.pgn', '../resources/tournaments/carlsbad1911.pgn']
    tFolder = '../resources/tournaments'
    pgns = [f'{tFolder}/{fileName}' for fileName in os.listdir(tFolder)]
    # outFile = '../out/bookMoves1980-2000.pkl'
    # outFile = '../out/bookMoves1910-29.pkl'
    # outFile = '../out/bookMovesByYear.pkl'
    pgn = '../resources/top20games1980-2026.pgn'
    outFile = '../out/bookMovesTop20_1980-2026.pkl'
    # outFile = '../out/bookMoves2012-2026.pkl'
    # data = getBookMovesPerYear([pgn], script, db)
    # data = getBookMovesPerYear(pgns, script, db)
    # pickle.dump(data, open(outFile, 'wb+'))
    # data = pickle.load(open(outFile, 'rb'))
    top100files = ['../out/bookMoves1980-1993.pkl', '../out/bookMoves1994-2011.pkl', '../out/bookMoves2012-2026.pkl']
    top50files = ['../out/bookMovesTop50_1980-1999.pkl', '../out/bookMovesTop50_2000-2015.pkl', '../out/bookMovesTop50_2016-2026.pkl']
    top20files = ['../out/bookMovesTop20_1980-2026.pkl']
    plotOpeningData(top100files, 'Number of moves until the first new position in games between players in the top 100', filename='../out/bookMovesTop100.png')
    plotOpeningData(top50files, 'Number of moves until the first new position in games between players in the top 50', filename='../out/bookMovesTop50.png')
    plotOpeningData(top20files, 'Number of moves until the first new position in games between players in the top 20', filename='../out/bookMovesTop20.png')
    plotDifferentPlayerGroups([top100files, top50files, top20files], 'Average number of moves before reaching a new position for different levels', ['Top 100', 'Top 50', 'Top 20'], filename='../out/bookMovesAvg.png')
    """
    analyseOpeningData(data)
    for k, v in data.items():
        if len(v) == 0:
            print(k)
        else:
            print(k, sum(v)/len(v))
    """
