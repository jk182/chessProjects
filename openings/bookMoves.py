import chess
import chess.pgn
import subprocess

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper

import matplotlib.pyplot as plt


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

if __name__ == '__main__':
    db = '/Users/julian/Library/Mobile Documents/com~apple~CloudDocs/chessDB'
    script = 'searchPosition.tcl'
    pgn = '../resources/vanForeest-gukesh.pgn'
    moveScript = 'getMoveFrequencies.tcl'
    # getBookMoves(pgn, moveScript, db)
    najdorf = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'
    # print(getMoveStatistics(db, moveScript, najdorf, '2025.01.01'))
    prague = '../resources/tournaments/prague2026.pgn'
    plotTimeSpentPerPlayer(prague, 40)
