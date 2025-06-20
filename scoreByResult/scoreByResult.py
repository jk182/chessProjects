import chess
import pandas as pd
from chess import pgn


def getGameData(pgnPath: str) -> pd.DataFrame:
    timeControl = ""
    totalGames = 0

    data = {'White': list(), 'Black': list(), 'WhiteElo': list(), 'BlackElo': list(), 'Result': list(), 'Date': list(), 'TimeControl': list(), 'Event': list(), 'Round': list()}
    with open(pgnPath, 'r', encoding='utf8') as pgn:
        while game := chess.pgn.read_game(pgn):
            event = game.headers['Event']
            if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                continue
            if 'blitz' in event.lower() or 'armageddon' in event.lower() or 'FIDE World Bl' in event or 'ICC' in event or 'TB' in event or 'Carlsen-Ding Showdown' in event:
                timeControl = 'blitz'
            elif 'rapid' in event.lower() or 'cct' in event.lower() or 'speedchess' in event.lower() or 'gcl' in event.lower() or 'FTX Crypto Cup 2022' in event or 'Oslo Esports Cup 2022' in event or 'Global Chess League' in event or 'Cuadrangular UNAM 2012' in event or 'Uva Four player KO 2014' in event:
                timeControl = 'rapid'
            elif 'freestyle' in event.lower() or 'fischer random' in event.lower() or 'chess960' in event.lower() or 'Play Live Challenge 2016' in event:
                continue
            else:
                totalGames += 1
                timeControl = 'classical'

            data['White'].append(game.headers['White'])
            data['Black'].append(game.headers['Black'])
            data['WhiteElo'].append(game.headers['WhiteElo'])
            data['BlackElo'].append(game.headers['BlackElo'])
            data['Result'].append(game.headers['Result'])
            data['Date'].append(game.headers['Date'])
            data['TimeControl'].append(timeControl)
            data['Event'].append(event)
            data['Round'].append(game.headers['Round'])
    print(totalGames)
    return pd.DataFrame(data)


def getScoreByPrevResult(df: pd.DataFrame, player: str) -> list:
    df = df.sort_values(by=['Date', 'Round'])
    lastEvent = None
    lastRound = None
    lastResult = None

    scoreByResult = {'Win': [0, 0, 0], 'Draw': [0, 0, 0], 'Loss': [0, 0, 0]}

    for i, row in df.iterrows():
        event = row['Event']
        if 'World Cup' in event and int(row['Round'].split('.')[1]) > 2:
            continue

        if (res := row['Result']) == '1/2-1/2':
            result = res
        elif (res == '1-0' and player in row['White']) or (res == '0-1' and player in row['Black']):
            result = '1-0'
        elif (res == '1-0' and player in row['Black']) or (res == '0-1' and player in row['White']):
            result = '0-1'
        else:
            print('Result not found!')
            continue

        if player in row['White']:
            oppRating = int(row['BlackElo'])
        else:
            oppRating = int(row['WhiteElo'])

        if '.' in row['Round']:
            roundNr = int(row['Round'].split('.')[0])
        else:
            roundNr = int(row['Round'])
        if lastEvent is None:
            lastEvent = event
            lastRound = roundNr
            lastResult = result
            continue

        if event == lastEvent and row['TimeControl'] == 'classical':
            if result == '1-0':
                points = 1
            elif result == '1/2-1/2':
                points = 0.5
            else:
                points = 0
            if lastResult == '1-0':
                scoreByResult['Win'][0] += points
                scoreByResult['Win'][1] += 1
                scoreByResult['Win'][2] += oppRating
            elif lastResult == '1/2-1/2':
                scoreByResult['Draw'][0] += points
                scoreByResult['Draw'][1] += 1
                scoreByResult['Draw'][2] += oppRating
            else:
                scoreByResult['Loss'][0] += points
                scoreByResult['Loss'][1] += 1
                scoreByResult['Loss'][2] += oppRating
        lastEvent = event
        lastRound = roundNr
        lastResult = result
    print(scoreByResult)
    for k, v in scoreByResult.items():
        score = v[0]/v[1]
        perfRating = v[2]/v[1] + (score-0.5) * 800
        print(f'{k}: {score}, {perfRating}')

if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    df = getGameData(carlsenGames)
    getScoreByPrevResult(df, 'Carlsen')
