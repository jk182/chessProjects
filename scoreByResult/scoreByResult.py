import chess
import pandas as pd
from chess import pgn


def getGameData(pgnPath: str) -> pd.DataFrame:
    timeControl = ""

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
            elif 'freestyle' in event.lower() or 'fischer random' in event.lower() or 'chess960' in event.lower():
                continue
            else:
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
    return pd.DataFrame(data)


def getScoreByPrevResult(df: pd.DataFrame) -> list:
    df = df.sort_values(by=['Date', 'Round'])
    lastEvent = None
    lastRound = None
    lastResult = None

    events = set()
    for i, row in df.iterrows():
        event = row['Event']
        result = row['Result']

        if event == 'GRENKE Chess Classic 2024':
            print(row)
        if '.' in row['Round']:
            r = int(row['Round'].split('.')[0])
        else:
            r = int(row['Round'])
        if lastEvent is None:
            lastEvent = event
            lastRound = r
            lastResult = result
            continue

        if event == lastEvent and r != lastRound + 1 and row['TimeControl'] == 'classical':
            # print(row)
            events.add(event)
        lastEvent = event
        lastRound = r
    print(events)


if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    df = getGameData(carlsenGames)
    getScoreByPrevResult(df)
