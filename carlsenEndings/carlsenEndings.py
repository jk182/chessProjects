import chess
from chess import pgn
import os, sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from functions import configureEngine
import pickle


def getEqualEndgameData(pgnPath: str, cachePath: str = None) -> pd.DataFrame:
    totalGames = 0
    blitzGames = 0
    rapidGames = 0
    chess960Games = 0
    endings = 0
    gameScore = [0, 0]
    cache = dict()

    players = dict()
    data = {'Player': list(), 'FEN': list(), 'Evaluation': list(), 'Opponent Rating': list(), 'Result': list(), 'Date': list()}

    if cachePath:
        with open(cachePath, 'rb') as pick:
            cache = pickle.load(pick)

    stockfish = configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    with open(pgnPath, 'r', encoding='utf8') as pgn:
        while game := chess.pgn.read_game(pgn):
            totalGames += 1
            event = game.headers['Event']
            if 'blitz' in event.lower():
                blitzGames += 1
            elif 'rapid' in event.lower():
                rapidGames += 1
            elif 'freestyle' in event.lower() or 'fischer random' in event.lower() or 'chess960' in event.lower():
                chess960Games += 1
            else:
                board = chess.Board()
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
                                else:
                                    data['Opponent Rating'].append(0)
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
        Dictionary indexed by years containing a list with [totalPoints, totalGames, perfRating]
    """
    yearlyData = dict()
    for i, row in df.iterrows():
        if playerName in row['Player']:
            year = int(row['Date'][:4])
            if year not in yearlyData.keys():
                yearlyData[year] = [0, 0, 0]
            yearlyData[year][0] += row['Result']
            yearlyData[year][1] += 1
            yearlyData[year][2] += row['Opponent Rating'] + (row['Result'] - 0.5) * 800

    # Normalizing the performance rating
    for year in yearlyData.keys():
        yearlyData[year][2] /= yearlyData[year][1]
    return dict(sorted(yearlyData.items()))


if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    otherGames = '../out/2700games2023-out.pgn'
    cacheP = '../resources/endingsCache.pickle'
    data = getEqualEndgameData(carlsenGames, cachePath='../resources/carslenEndingsCache.pickle')
    print(getPlayerScoreByYear(data, 'Carlsen, M'))
    # getEqualEndgameData(otherGames, cachePath=cacheP)
    # getEqualEndgameData('../resources/2650games2022.pgn', cachePath=cacheP)
    # for path in ['../resources/nakaGames.pgn', '../resources/adamsGames.pgn', '../resources/rubinsteinGames.pgn', '../resources/capablancaGames.pgn']:
    # for path in ['../resources/mvlGames.pgn', '../resources/nepoGames1.pgn']:
    #     getEqualEndgameData(path, cacheP)
