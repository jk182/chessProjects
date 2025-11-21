import chess
import chess.pgn
import io


def extractGamesByRating(ratingBands: list, gamesPerBand: int, maxRatingDiff: int = 50, outPath: str = '../out/lichessDB/rating'):
    pgns = list()
    pgns = [""] * len(ratingBands)
    nGames = [0] * len(ratingBands)
    nextIsEnd = False
    pgn = ""
    wElo = None
    bElo = None
    ratingIndex = None
    date = None

    while True:
        line = input()
        pgn = f'{pgn}{line.strip()}\n'
        if "[WhiteElo " in line:
            wElo = int(line.split('"')[1])
        if "[BlackElo " in line:
            bElo = int(line.split('"')[1])
            if abs(wElo-bElo) <= maxRatingDiff and (wElo+bElo)/2 >= ratingBands[0]:
                ratingIndex = len(ratingBands)-1
                for i in range(len(ratingBands)-1):
                    if ratingBands[i] <= (wElo+bElo)/2 < ratingBands[i+1]:
                        ratingIndex = i
                        break
            else:
                ratingIndex = None
        if '[WhiteTitle "BOT"]' in line or '[BlackTitle "BOT"]' in line:
            ratingIndex = None
        if 'TimeControl' in line:
            if line.split('"')[1] == '-':
                ratingIndex = None
            elif int(line.split('"')[1].split('+')[0]) < 180:
                ratingIndex = None
        if 'UTCDate' in line:
            date = line.split('"')[1]
        if not line.strip():
            if nextIsEnd:
                if ratingIndex is not None and nGames[ratingIndex] < gamesPerBand:
                    pgns[ratingIndex] += f'{pgn}\n'
                    nGames[ratingIndex] += 1
                    print(ratingBands[ratingIndex], nGames[ratingIndex], date)
                    end = True
                    for g in nGames:
                        if g < gamesPerBand:
                            end = False
                            break
                    if end:
                        for i, r in enumerate(ratingBands):
                            with open(f'{outPath}{r}.pgn', 'w+') as f:
                                print(pgns[i], file=f)
                        """
                        for p in pgns:
                            f = io.StringIO(p)
                            while game := chess.pgn.read_game(f):
                                print(game)
                        """
                        print('Finished')
                        return pgns
                pgn = ""
                nextIsEnd = False
            else:
                nextIsEnd = True

    return pgns


def extractAnalysedGames(ratings: list, gamesPerBand: int, timeControls: list, maxPlayerRatingDiff: int = 50, maxRatingDeviation: int = 100, outPath: str = '../out/lichessDB/analysed_300g_rating'):
    """
    I want that the average rating of the players is close to the rating given, not a rating band as before
    """
    nextIsEnd = False
    pgn = ""
    wElo = None
    bElo = None
    ratingIndex = None
    date = None
    hasEval = False
    tcIndex = None
    nGames = list()
    for r in ratings:
        nGames.append([0] * len(timeControls))

    while True:
        line = input()
        pgn = f'{pgn}{line.strip()}\n'
        if "[WhiteElo " in line:
            wElo = int(line.split('"')[1])
        if "[BlackElo " in line:
            bElo = int(line.split('"')[1])
            avgElo = (wElo+bElo)/2
            if abs(wElo-bElo) <= maxPlayerRatingDiff:
                for i in range(len(ratings)):
                    if abs(ratings[i] - avgElo) < maxRatingDeviation:
                        ratingIndex = i
                        break

        if '[WhiteTitle "BOT"]' in line or '[BlackTitle "BOT"]' in line:
            ratingIndex = None
        if 'TimeControl' in line:
            tc = line.split('"')[1]
            if tc == '-':
                ratingIndex = None
            elif tc in timeControls:
                tcIndex = timeControls.index(tc)
            else:
                tcIndex = None
        if 'UTCDate' in line:
            date = line.split('"')[1]
        if '%eval' in line:
            hasEval = True
        if not line.strip():
            if nextIsEnd:
                if ratingIndex is not None and tcIndex is not None and nGames[ratingIndex][tcIndex] < gamesPerBand and hasEval:
                    nGames[ratingIndex][tcIndex] += 1
                    print(ratings[ratingIndex], timeControls[tcIndex], nGames[ratingIndex][tcIndex], date)
                    with open(f'{outPath}{ratings[ratingIndex]}_{timeControls[tcIndex]}.pgn', 'a+') as f:
                        print(f'{pgn}\n', file=f)
                    end = True
                    for games in nGames:
                        for g in games:
                            if g < gamesPerBand:
                                end = False
                                break
                    if end:
                        print('Finished')
                        return
                pgn = ""
                nextIsEnd = False
                hasEval = False
                tcIndex = None
                ratingIndex = None
            else:
                nextIsEnd = True



# extractGamesByRating([1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600], 5000)
# extractGamesByRating([2600, 2700], 5000, maxRatingDiff=80)
# extractAnalysedGames([1200, 1600, 2000, 2400], 2000, ["60+0", "180+0", "300+0", "600+0"])
extractAnalysedGames([2600], 3000, ["60+0", "120+1", "180+0", "180+2", "300+0", "300+3", "600+0"])
