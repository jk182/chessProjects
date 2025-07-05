import chess
import pandas as pd
from chess import pgn
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import plotting_helper


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
            elif 'World Cup' in event and int(game.headers['Round'].split('.')[1]) > 4:
                timeControl = 'blitz'
            elif 'World Cup' in event and int(game.headers['Round'].split('.')[1]) > 2:
                timeControl = 'rapid'
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
            data['Round'].append(float(game.headers['Round']))
    df = pd.DataFrame(data)
    df = df.sort_values(by=['Date', 'Round'])
    return df


def getScoreByPrevResult(df: pd.DataFrame, player: str) -> tuple:
    df = df.sort_values(by=['Date', 'Round'])
    lastEvent = None
    lastRound = None
    lastResult = None
    lastTC = None

    colorScore = [[[0, 0], [0, 0]], [[0, 0], [0, 0]], [[0, 0], [0, 0]]]

    scoreByResult = {'Win': [[0, 0, 0], [0, 0, 0], [0, 0, 0]], 'Draw': [[0, 0, 0], [0, 0, 0], [0, 0, 0]], 'Loss': [[0, 0, 0], [0, 0, 0], [0, 0, 0]]}

    for i, row in df.iterrows():
        event = row['Event']

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

        """
        if '.' in row['Round']:
            roundNr = int(row['Round'].split('.')[0])
        else:
            roundNr = int(row['Round'])
        """
        roundNr = int(row['Round'])
        tc = row['TimeControl']
        if lastEvent is None:
            lastEvent = event
            lastRound = roundNr
            lastResult = result
            lastTC = tc
            continue

        if event == lastEvent and tc == lastTC:
            tcindex = ['classical', 'rapid', 'blitz'].index(tc)
            if result == '1-0':
                points = 1
            elif result == '1/2-1/2':
                points = 0.5
            else:
                points = 0
            if lastResult == '1-0':
                scoreByResult['Win'][tcindex][0] += points
                scoreByResult['Win'][tcindex][1] += 1
                scoreByResult['Win'][tcindex][2] += oppRating
            elif lastResult == '1/2-1/2':
                scoreByResult['Draw'][tcindex][0] += points
                scoreByResult['Draw'][tcindex][1] += 1
                scoreByResult['Draw'][tcindex][2] += oppRating
            else:
                scoreByResult['Loss'][tcindex][0] += points
                scoreByResult['Loss'][tcindex][1] += 1
                scoreByResult['Loss'][tcindex][2] += oppRating
                if player in row['White']:
                    colorScore[tcindex][0][0] += points
                    colorScore[tcindex][0][1] += 1
                else:
                    colorScore[tcindex][1][0] += points
                    colorScore[tcindex][1][1] += 1
        lastEvent = event
        lastRound = roundNr
        lastResult = result
        lastTC = tc
    # print(scoreByResult)
    for w, b in colorScore:
        print(w[0]/w[1], b[0]/b[1])
        print(w[1]/(w[1]+b[1]))
    scoreList = [list(), list(), list()]
    perfRatings = [list(), list(), list()]
    for k, val in scoreByResult.items():
        for i, v in enumerate(val):
            score = v[0]/v[1]
            scoreList[i].append(score)
            perfRating = v[2]/v[1] + (score-0.5) * 800
            perfRatings[i].append(perfRating)
            # print(f'{k}: {score}, {perfRating}')
    # print(scoreList)
    return (scoreList, perfRatings)


if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    df = getGameData(carlsenGames)
    sl, pr = getScoreByPrevResult(df, 'Carlsen')
    print(pr)
    # plotting_helper.plotPlayerBarChart(sl, ['Classical', 'Rapid', 'Blitz'], 'Score', "Carlsen's score based on the previous result", ['After a win', 'After a draw', 'After a loss'], colors=plotting_helper.getColors(['green', 'blue', 'orange']), filename='../out/scoreBasedOnResult.png')
    # plotting_helper.plotPlayerBarChart(pr, ['Classical', 'Rapid', 'Blitz'], 'Performance rating', "Carlsen's performance rating based on the previous result", ['After a win', 'After a draw', 'After a loss'], colors=plotting_helper.getColors(['green', 'blue', 'orange']), filename='../out/perfRatingBasedOnResult.png')
