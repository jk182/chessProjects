import chess

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotting_helper

import polars as pl
import pickle
import itertools


def extractGameData(pgnPaths: list, matchNames: list) -> pl.DataFrame:
    keys = ['Match', 'GameNr', 'White', 'Black', 'WhiteElo', 'BlackElo', 'Result', 'WhiteAccuracy', 'BlackAccuracy', 'XSLperMove', 'MoveNr', 'Moves']
    data = dict()
    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                xsl = [list(), list()]
                node = game
                moves = [m.uci() for m in game.mainline_moves()]
                ply = 1
                lastXs = functions.expectedScore(20)
                while not node.is_end():
                    ply += 1
                    node = node.variations[0]
                    if node.comment:
                        xs = functions.expectedScore(functions.readComment(node, True, True)[1])
                    else:
                        continue
                    if node.board().turn:
                        xsl[1].append(max(0, xs - lastXs))
                    else:
                        xsl[0].append(max(0, lastXs - xs))
                    lastXs = xs
                
                white = game.headers["White"]
                black = game.headers["Black"]
                if "WhiteElo" in game.headers:
                    wElo = int(game.headers["WhiteElo"])
                else:
                    wElo = 0

                if "BlackElo" in game.headers:
                    bElo = int(game.headers["BlackElo"])
                else:
                    bElo = 0

                matchName = None
                for m in matchNames:
                    if white.split(',')[0].split()[0] in m and black.split(',')[0].split()[0] in m and game.headers["Date"][:4] in m:
                        matchName = m
                        break
                if matchName is None:
                    print(white, black)

                d = [matchName, 
                     int(game.headers["Round"].split('.')[0]),
                     white,
                     black,
                     wElo,
                     bElo,
                     game.headers["Result"],
                     functions.gameAccuracy(sum(xsl[0])/len(xsl[0])),
                     functions.gameAccuracy(sum(xsl[1])/len(xsl[1])),
                     sum(itertools.chain(xsl[0], xsl[1]))/len(list(itertools.chain(xsl[0], xsl[1]))),
                     ply//2,
                     moves]

                for i, key in enumerate(data.keys()):
                    data[key].append(d[i])

    return pl.DataFrame(data)


def extractMoveData(gamePaths: list, matchNames: list) -> pl.DataFrame:
    keys = ['Match', 'GameNr', 'White', 'Black', 'Move', 'Ply', 'Turn', 'XSbefore', 'XSafter', 'complexityBefore', 'complexityAfter']
    data = dict()
    for key in keys:
        data[key] = list()

    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                white = game.headers["White"]
                black = game.headers["Black"]

                matchName = None
                for m in matchNames:
                    if white.split(',')[0].split()[0] in m and black.split(',')[0].split()[0] in m and game.headers["Date"][:4] in m:
                        matchName = m
                        break
                if matchName is None:
                    print(white, black)

                gameNr = int(game.headers["Round"].split('.')[0])

                node = game
                ply = 0
                lastXs = functions.expectedScore(20)
                lastComp = functions.lc0Rescale([220, 614, 166])
                while not node.is_end():
                    ply += 1
                    node = node.variations[0]
                    if node.comment:
                        comp = functions.lc0Rescale(functions.readComment(node, True, True)[0])
                        xs = functions.expectedScore(functions.readComment(node, True, True)[1])
                    else:
                        print(matchName, ply)
                        continue

                    if node.board().turn:
                        xsl = max(0, xs - lastXs)
                        turn = False
                    else:
                        xsl = max(0, lastXs - xs)
                        turn = True

                    d = [matchName,
                         gameNr,
                         white,
                         black,
                         '',
                         ply,
                         turn, 
                         lastXs,
                         xs,
                         lastComp,
                         comp]

                    for i, key in enumerate(data.keys()):
                        data[key].append(d[i])
                
                    lastXs = xs
                    lastComp = comp

    return pl.DataFrame(data)


def plotGameData(gameData: pl.DataFrame, rowName: str):
    plotData = dict()
    for row in gameData.iter_rows(named=True):
        if (match := row['Match']) not in plotData:
            plotData[match] = list()

        plotData[match].append(row[rowName])

    plotData = dict(sorted(plotData.items(), key=lambda x: int(x[0][-4:])))
    plotting_helper.plotBoxplot(list(plotData.values()), 'Match', 'Game length', 'Game lenghts for each WCC match', xTickLabels=[m.split(',')[0].replace('Nepomniachtchi', 'Nepo') for m in plotData.keys()])


def plotGameDataAsScatterPlot(gameData: pl.DataFrame):
    plotData = dict()
    for row in gameData.iter_rows(named=True):
        if (match := row['Match']) not in plotData:
            plotData[match] = list()

        plotData[match].append((row['XSLperMove'], row['MoveNr']))

    plotData = dict(sorted(plotData.items(), key=lambda x: int(x[0][-4:])))
    pdMoves = dict()
    pdGames = dict()
    for k, v in plotData.items():
        pdMoves[k] = sum([x[0]*x[1] for x in v])/sum([x[1] for x in v])
        pdGames[k] = sum([x[0]*x[1] for x in v])/(len(v)*100)

    plotting_helper.plotScatterPlot([[int(m[-4:]) for m in pdMoves.keys()]]*2, [list(pdMoves.values()), list(pdGames.values())], 'Match', 'Expected score loss per move', 'Expected score loss per move')


def plotGameResults(gameData: pl.DataFrame):
    plotData = dict()
    for row in gameData.iter_rows(named=True):
        if (match := row['Match']) not in plotData:
            plotData[match] = [0, 0, 0]

        if (result := row['Result']) == '1-0':
            plotData[match][0] += 1
        elif result == '1/2-1/2':
            plotData[match][1] += 1
        elif result == '0-1':
            plotData[match][2] += 1

    plotData = dict(sorted(plotData.items(), key=lambda x: int(x[0][-4:])))
    plotting_helper.plotStackedBarChart(list(plotData.values()), '', '% of games', 'Relative number of game results', ['White\nwins', 'Draws', 'Black\nwins'], colors=['white', 'grey', 'black'], xTickLabels=[f'{m.split(",")[0].replace("Nepomniachtchi", "Nepo")},{m[-2:]}' for m in plotData.keys()], legendOnRight=True)


def plotFirstMoves(gameData: pl.DataFrame):
    plotData = dict()
    moves = ['e2e4', 'd2d4', 'c2c4', 'g1f3', 'g2g3']
    for row in gameData.iter_rows(named=True):
        if (match := row['Match']) not in plotData:
            plotData[match] = [0 for _ in moves]

        firstMove = row['Moves'][0]
        if firstMove in moves:
            plotData[match][moves.index(firstMove)] += 1
        else:
            print(firstMove)

    plotData = dict(sorted(plotData.items(), key=lambda x: int(x[0][-4:])))
    pd = dict()
    for m, v in plotData.items():
        pd[m] = [x/sum(v) for x in v]

    plotting_helper.plotStackedBarChart(list(pd.values()), '', '% of games', 'Relative number of each opening move', ['1.e4', '1.d4', '1.c4', '1.Nf3', '1.g3'], xTickLabels=[f'{m.split(",")[0].replace("Nepomniachtchi", "Nepo")},{m[-2:]}' for m in plotData.keys()], legendOnRight=True)


def findLongestResultStreaks(results: dict) -> list:
    streaks = list()
    for data in results.values():
        currentStreak = 0
        currentStreakIndex = -1
        longestStreaks = [0, 0, 0, 0]
        nextStreakIndex = -1
        lastStreak = 0
        for i, d in enumerate(data[:-1]):
            if currentStreakIndex == -1:
                currentStreakIndex = int(2-2*d)
                currentStreak += 1

            if d == data[i+1]:
                if currentStreakIndex == int(2-2*d):
                    currentStreak += 1
                else:
                    longestStreaks[currentStreakIndex] = max(longestStreaks[currentStreakIndex], currentStreak)
                    currentStreak = 2
                    currentStreakIndex = int(2-2*d)
            elif abs(d-data[i+1]) == 1:
                longestStreaks[0] = max(longestStreaks[0], 1)
                longestStreaks[2] = max(longestStreaks[2], 1)
                if currentStreakIndex == 3 or currentStreak == 1:
                    currentStreak += 1
                    currentStreakIndex = 3
                else:
                    longestStreaks[currentStreakIndex] = max(longestStreaks[currentStreakIndex], currentStreak)
                    currentStreakIndex = 3
                    currentStreak = 2
            else:
                longestStreaks[currentStreakIndex] = max(longestStreaks[currentStreakIndex], currentStreak)
                currentStreakIndex = -1
                currentStreak = 0

        if data[-1] == 1:
            index = 0
        elif data[-1] == 0.5:
            index = 1
        else:
            index = 2

        if data[-1] != data[-2] and abs(data[-1] - data[-2]) != 1:
            currentStreak = 1
        
        longestStreaks[index] = max(longestStreaks[index], currentStreak)

        streaks.append(longestStreaks)
    return streaks


def analyseMatchTrajectory(gameData: pl.DataFrame):
    matchData = dict()
    gameLengths = dict()
    for row in gameData.iter_rows(named=True):
        if (match := row['Match']) not in matchData:
            matchData[match] = list()
            gameLengths[match] = list()

        gameNr = row['GameNr']
        gameLength = row['MoveNr']

        if (result := row['Result']) == '1/2-1/2':
            points = 0.5
        elif match.split('-')[0] in row["White"]:
            if result == '1-0':
                points = 1
            else:
                points = 0
        else:
            if result == '1-0':
                points = 0
            else:
                points = 1

        if gameNr <= len(matchData[match]):
            matchData[match][gameNr-1] = points
            gameLengths[match][gameNr-1] = gameLength
        else:
            nl = [0 for _ in range(gameNr-len(matchData[match]))]
            nl[-1] = points
            matchData[match].extend(nl)
            nl[-1] = gameLength
            gameLengths[match].extend(nl)

    matchData = dict(sorted(matchData.items(), key=lambda x: int(x[0][-4:])))
    
    pData = [[sum([int(2*x-1) for x in d[:i+1]]) for i in range(len(d))] for d in matchData.values()]

    biggestDeficit = min([min(d) for d in pData])
    print(f'Biggest overcome deficit: {biggestDeficit} in {[m for i, m in enumerate(list(matchData.keys())) if min(pData[i]) == biggestDeficit]}')

    latestComeback = min([d[::-1].index(-1) if -1 in d else len(d) for d in pData])
    print(f'Latest overcome deficit: {latestComeback} in {[m for i, m in enumerate(list(matchData.keys())) if pData[i][::-1][latestComeback] == -1]}')

    streaks = findLongestResultStreaks(matchData)
    names = ['winning', 'drawing', 'losing', 'back-and-forth']
    for i in range(4):
        streak = [s[i] for s in streaks]
        l = max(streak)
        print(f'Longest {names[i]} streak: {l} in {[m for j, m in enumerate(list(matchData.keys())) if streak[j] == l]}')

    longestGames = [max(v) for v in gameLengths.values()]
    print(longestGames)
    
    # plotting_helper.plotLineChartSingleX(pData, 'Game number', 'Score of eventual winner', 'Score of the eventual winner by game number', list(matchData.keys()))


def plotComplexity(moveData: dict):
    data = dict()
    for row in moveData.iter_rows(named=True):
        if (match := row['Match']) not in data:
            data[match] = list()

        # data[match].append(row['complexityBefore'])
        data[match].append(row['complexityAfter']-row['complexityBefore'])

    data = dict(sorted(data.items(), key=lambda x: int(x[0][-4:])))

    plotData = list()
    for k, v in data.items():
        plotData.append(sum(v)/len(v))

    plotting_helper.plotScatterPlot([[int(m[-4:]) for m in data.keys()]], [plotData], 'Match', 'Average complexity', 'Average complexity for each match')


def findOpeningDeviations(gameData: pl.DataFrame):
    data = dict()
    for row in gameData.iter_rows(named=True):
        if (match := row['Match']) not in data:
            data[match] = list()

        gameNr = row["GameNr"]
        if gameNr <= len(data[match]):
            data[match][gameNr-1] = (row["White"], row["Black"], row["Moves"])
        else:
            nl = [("", "", []) for _ in range(gameNr-len(data[match]))]
            nl[-1] = (row["White"], row["Black"], row["Moves"])
            data[match].extend(nl)

    data = dict(sorted(data.items(), key=lambda x: int(x[0][-4:])))

    for match, d in data.items():
        print(match)
        moves = [x[2] for x in d]
        for i, m in enumerate(moves):
            players = (d[i][0], d[i][1])
            repeated = False
            for j in range(1, len(m)):
                if m[:j] not in [x[:j] for x in moves[:i]]:
                    player = players[(j-1)%2]
                    print(f'{j-1} moves repeated in game {i+1}, {player} deviated')
                    repeated = True
                    break

if __name__ == '__main__':
    matchNames = ['Steinitz-Zukertort, 1886', 'Steinitz-Chigorin, 1889', 'Steinitz-Gunsberg, 1890', 'Steinitz-Chigorin, 1892', 
                  'Lasker-Steinitz, 1894', 'Lasker-Steinitz, 1896', 'Lasker-Marshall, 1907', 'Lasker-Tarrasch, 1908', 'Lasker-Schlechter, 1910',
                  'Lasker-Janowski, 1910', 'Capablanca-Lasker, 1921', 'Alekhine-Capablanca, 1927', 'Alekhine-Bogoljubow, 1929', 
                  'Alekhine-Bogoljubow, 1934', 'Euwe-Alekhine, 1935', 'Alekhine-Euwe, 1937', 'Botvinnik-Bronstein, 1951', 'Botvinnik-Smyslov, 1954',
                  'Smyslov-Botvinnik, 1957', 'Botvinnik-Smyslov, 1958', 'Tal-Botvinnik, 1960', 'Botvinnik-Tal, 1961', 'Petrosian-Botvinnik, 1963', 
                  'Petrosian-Spassky, 1966', 'Spassky-Petrosian, 1969', 'Fischer-Spassky, 1972', 'Karpov-Korchnoi, 1978', 
                  'Karpov-Korchnoi, 1981', 'Karpov-Kasparov, 1984', 'Kasparov-Karpov, 1985', 'Kasparov-Karpov, 1986', 'Kasparov-Karpov, 1987',
                  'Kasparov-Karpov, 1990', 'Kasparov-Short, 1993', 'Kasparov-Anand, 1995', 'Kramnik-Kasparov, 2000', 'Kramnik-Leko, 2004', 
                  'Kramnik-Topalov, 2006', 'Anand-Kramnik, 2008', 'Anand-Topalov, 2010', 'Anand-Gelfand, 2012', 'Carlsen-Anand, 2013',
                  'Carlsen-Anand, 2014', 'Carlsen-Karjakin, 2016', 'Carlsen-Caruana, 2018', 'Carlsen-Nepomniachtchi, 2021', 
                  'Ding-Nepomniachtchi, 2023', 'Gukesh-Ding, 2024']
    pgnPaths = ['../out/wcc1886-1908_analysed.pgn', '../out/wcc1910-1921_analysed.pgn', '../out/wcc1927-1929_analysed.pgn', '../out/wcc1934-1960_analysed.pgn', '../out/wcc1961-1981_analysed.pgn', '../out/wcc1984-1995_analysed.pgn', '../out/wcc2000-2024_analysed.pgn']
    mDataPath = '../out/wccMatchData.pkl'
    moveDataPath =  '../out/wccMoveData.pkl'

    """
    wccMatchData = extractGameData(pgnPaths, matchNames)
    with open(mDataPath, 'wb+') as f:
        pickle.dump(wccMatchData, f)
    """

    with open(mDataPath, 'rb') as f:
        wccMatchData = pickle.load(f)

    """
    wccMoveData = extractMoveData(pgnPaths, matchNames)
    with open(moveDataPath, 'wb+') as f:
        pickle.dump(wccMoveData, f)
    """

    with open(moveDataPath, 'rb') as f:
        wccMoveData = pickle.load(f)


    # plotGameData(wccMatchData, 'MoveNr')
    # plotGameData(wccMatchData, 'WhiteAccuracy')
    # plotGameData(wccMatchData, 'BlackAccuracy')
    # plotGameData(wccMatchData, 'XSLperMove')

    # plotGameDataAsScatterPlot(wccMatchData)

    # plotGameResults(wccMatchData)

    # analyseMatchTrajectory(wccMatchData)

    # plotComplexity(wccMoveData)

    # plotFirstMoves(wccMatchData)

    findOpeningDeviations(wccMatchData)
