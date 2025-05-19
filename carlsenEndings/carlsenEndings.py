import chess
from chess import pgn
import os, sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from functions import configureEngine
import plotting_helper
import pickle
import matplotlib.pyplot as plt

def getEqualEndgameData(pgnPath: str, cachePath: str = None) -> pd.DataFrame:
    totalGames = 0
    blitzGames = 0
    rapidGames = 0
    chess960Games = 0
    endings = 0
    gameScore = [0, 0]
    cache = dict()

    players = dict()
    data = {'Player': list(), 'FEN': list(), 'Evaluation': list(), 'Player Rating': list(), 'Opponent Rating': list(), 'Result': list(), 'Date': list()}

    if cachePath:
        with open(cachePath, 'rb') as pick:
            cache = pickle.load(pick)

    stockfish = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    with open(pgnPath, 'r', encoding='utf8') as pgn:
        while game := chess.pgn.read_game(pgn):
            totalGames += 1
            event = game.headers['Event']
            if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                continue
            if 'blitz' in event.lower() or 'armageddon' in event.lower() or 'FIDE World Bl' in event:
                blitzGames += 1
            elif 'rapid' in event.lower() or 'cct' in event.lower() or 'speedchess' in event.lower() or 'gcl' in event.lower() or 'FTX Crypto Cup 2022' in event or 'Oslo Esports Cup 2022' in event:
                rapidGames += 1
            elif 'freestyle' in event.lower() or 'fischer random' in event.lower() or 'chess960' in event.lower():
                chess960Games += 1
            else:
                board = game.board()
                for move in game.mainline_moves():
                    if not board.is_legal(move):
                        break
                    board.push(move)
                    if not board.is_valid():
                        print('Illegal position')
                        print(game.headers)
                        break
                    if isEndgame(board):
                        fen = board.fen()
                        if fen in cache.keys():
                            score = cache[fen]
                        else:
                            info = stockfish.analyse(board, chess.engine.Limit(time=5))
                            if info['score'].is_mate():
                                print('Mate!')
                                score = 9999
                            else:
                                score = info['score'].white().score()
                            print(score)
                            cache[fen] = score
                        if abs(score) < 30:
                            # An equal endgame has been reached
                            gameScore[1] += 1
                            result = game.headers['Result']
                            white = game.headers['White']
                            black = game.headers['Black']
                            """
                            for player in [white, black]:
                                if player not in players.keys():
                                    players[player] = [0, 0]
                                players[player][1] += 1
                                if result == '1/2-1/2':
                                    players[player][0] += 0.5
                                elif (result == '1-0' and player == white) or (result == '0-1' and player == black):
                                    players[player][0] += 1
                            """
                            if result == '1-0':
                                results = [1, 0]
                            elif result == '0-1':
                                results = [0, 1]
                            else:
                                results = [0.5, 0.5]
                            for i in range(2):
                                data['Player'].append([white, black][i])
                                data['FEN'].append(fen)
                                data['Evaluation'].append(score)
                                if 'WhiteElo' in game.headers.keys() and 'BlackElo' in game.headers.keys():
                                    data['Opponent Rating'].append([int(game.headers['BlackElo']), int(game.headers['WhiteElo'])][i])
                                    data['Player Rating'].append([int(game.headers['WhiteElo']), int(game.headers['BlackElo'])][i])
                                else:
                                    data['Opponent Rating'].append(0)
                                    data['Player Rating'].append(0)
                                data['Result'].append(results[i])
                                data['Date'].append(game.headers['Date'])
                            """
                            if ('Carlsen' in white and result == '1-0') or ('Carlsen' in black and result == '0-1'):
                                gameScore[0] += 1
                            elif result == '1/2-1/2':
                                gameScore[0] += 0.5
                            """
                            """


                            if result == '1/2-1/2':
                                gameScore[0] += 0.5
                            else:
                                gameScore[0] += 1
                            print(gameScore)
                            """
                        if totalGames % 100 == 0:
                            if cachePath:
                                with open(cachePath, 'wb') as pick:
                                    pickle.dump(cache, pick)
                        endings += 1
                        break

    if cachePath:
        with open(cachePath, 'wb') as pick:
            pickle.dump(cache, pick)
    stockfish.quit()
    return pd.DataFrame(data)


def isEndgame(position: chess.Board) -> bool:
    """
    This function determins if a position is an endgame
    """
    pieces = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
    pieceCount = 0
    for piece in pieces:
        for color in [chess.WHITE, chess.BLACK]:
            pieceCount += len(list(position.pieces(piece, color)))
    return pieceCount <= 6


def getPlayerScoreByYear(df: pd.DataFrame, playerName: str) -> dict:
    """
    This calculates the score and rating performance for a player broken down by year
    df: pd.DataFrame
        Endgame data from getEqualEndgameData
    playerName: str
        The name of the player (only checked with in)
    return -> dict
        Dictionary indexed by years containing a list with [totalWins, totalPoints, totalGames, perfRating]
    """
    yearlyData = dict()
    for i, row in df.iterrows():
        if playerName in row['Player']:
            year = int(row['Date'][:4])
            if year not in yearlyData.keys():
                yearlyData[year] = [0, 0, 0, 0]
            if row['Result'] == 1:
                yearlyData[year][0] += 1
            yearlyData[year][1] += row['Result']
            yearlyData[year][2] += 1
            yearlyData[year][3] += row['Opponent Rating'] + (row['Result'] - 0.5) * 800

    # Normalizing the performance rating
    for year in yearlyData.keys():
        yearlyData[year][3] /= yearlyData[year][2]
    return dict(sorted(yearlyData.items()))


def chunkYearlyData(yearlyData: dict, chunkSize: int) -> dict:
    """
    This groups the yearly data into bigger chunks
    yearlyData: dict
        Dictionary from getPlayerScoreByYear
    chunkSize: int
        The number of years which should be grouped together
    return -> dict
        Dictionary indexed by year range (startYear-endYear) containing a list with [totalWins, totalPoints, totalGames, perfRating]
    """
    data = dict()
    startYear = 0
    currentData = [0, 0, 0, 0]
    for i, (year, d) in enumerate(yearlyData.items()):
        if i % chunkSize == 0:
            startYear = year
            currentData = [0, 0, 0, 0]
        for j in range(len(d)-1):
            currentData[j] += d[j]
        currentData[3] += d[3]*d[2]
        if i % chunkSize == chunkSize-1:
            currentData[3] /= currentData[2]
            data[f'{startYear}-{year}'] = currentData
    return data


def getPlayerScore(df: pd.DataFrame, playerName: str) -> tuple:
    """
    This claculates the score for one given player
    return -> tuple
        (score, relWins, relLosses)
    """
    scores = list()
    perfRating = 0
    for i, row in df.iterrows():
        if playerName in row['Player']:
            scores.append(row['Result'])
            perfRating += row['Opponent Rating'] + (row['Result'] - 0.5) * 800

    perfRating /= len(scores)
    print(perfRating)
    wins = [s for s in scores if s == 1]
    losses = [s for s in scores if s == 0]
    return (sum(scores)/len(scores), len(wins)/len(scores), len(losses)/len(scores))


def getRatingScore(df: pd.DataFrame) -> tuple:
    """
    This calculates the score for 2800 rated players
    return -> tuple
        (score, relWins, relLosses)
    """
    rating = 2800
    scores = list()
    perfRating = 0
    for i, row in df.iterrows():
        if row['Player Rating'] >= rating and row['Opponent Rating'] < 2800:
            scores.append(row['Result'])
            perfRating += row['Opponent Rating'] + (row['Result'] - 0.5) * 800

    perfRating /= len(scores)
    print(perfRating)
    wins = [s for s in scores if s == 1]
    losses = [s for s in scores if s == 0]
    return (sum(scores)/len(scores), len(wins)/len(scores), len(losses)/len(scores))


def plotEndgamePerformance(players: list, data: pd.DataFrame):
    fig, ax = plt.subplots(figsize = (10, 6))

    colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']
    ax.set_facecolor('#e6f7f2')


def plotWinLossData(data: list, labels: list, filename: str = None):
    """
    This plots the relative number of wins and losses
    data: list
        List of DataFrames to get the win and loss data
    labels: list
        The labels for the data
    """
    # Assume that the first data entry is for Carlsen and the second one for rating
    playerScore = getPlayerScore(data[0], 'Carlsen')
    print(playerScore)
    ratingScore = getRatingScore(data[1])
    plotData = [[playerScore[1], playerScore[2]], 
                [ratingScore[1], ratingScore[2]]]
    plotting_helper.plotPlayerBarChart(plotData, labels, 'Relative number of wins/losses', 'Relative number of wins and losses in equal endings', ['Win%', 'Loss%'], colors=plotting_helper.getColors(['green', 'red']), filename=filename)


def plotYearlyWinLossData(yearlyData: dict, title: str, filename: str = None):
    """
    This plots the relative number of wins and losses for the yearly data.
    Each year (or group of years) is plotted separately 
    """
    data = list()
    for year, d in yearlyData.items():
        winP = d[0]/d[2]
        # get losses by taking totalGames-wins-draws (with draws = (totalScore-wins)*2)
        lossP = (d[2]-d[0]-(d[1]-d[0])*2)/d[2]
        data.append([winP, lossP])
    plotting_helper.plotPlayerBarChart(data, yearlyData.keys(), 'Relative number of wins/losses', title, ['Win%', 'Loss%'], colors=plotting_helper.getColors(['green', 'red']), filename=filename)


if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    otherGames = '../out/2700games2023-out.pgn'
    cacheP = '../resources/endingsCache.pickle'
    games2800 = '../resources/2800Games.pgn'
    df2800 = getEqualEndgameData(games2800, cachePath='../resources/2800cache.pickle')
    print(getRatingScore(df2800))
    data = getEqualEndgameData(carlsenGames, cachePath='../resources/carslenEndingsCache.pickle')
    print(getPlayerScore(data, 'Carlsen'))
    plotWinLossData([data, df2800], ['Carlsen', '2800 players'], filename='../out/endgames/carlsenV2800.png')
    yearlyData = getPlayerScoreByYear(data, 'Carlsen')
    chunks = chunkYearlyData(yearlyData, 3)
    print(chunks)
    plotYearlyWinLossData(chunks, 'Carlsens relative number of wins and losses in equal endings over the years', filename='../out/endgames/carlsenYearly.png')

    # print(getPlayerScore(data, 'Carlsen, M'))
    # getEqualEndgameData(otherGames, cachePath=cacheP)
    # getEqualEndgameData('../resources/2650games2022.pgn', cachePath=cacheP)
    # for path in ['../resources/nakaGames.pgn', '../resources/adamsGames.pgn', '../resources/rubinsteinGames.pgn', '../resources/capablancaGames.pgn']:
    # for path in ['../resources/nepoGames.pgn']:
        # getEqualEndgameData(path, cacheP)
