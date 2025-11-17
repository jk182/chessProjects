import chess
import chess.pgn
import io


def extractGamesByRating(ratingBands: list, gamesPerBand: int, maxRatingDiff: int = 50, outPath: str = '../out/lichessDB/rating'):
    pgns = list()
    pgns = [""] * len(ratingBands)
    nGames = [1] * len(ratingBands)
    nextIsEnd = False
    pgn = ""
    wElo = None
    bElo = None
    ratingIndex = None

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
        if not line.strip():
            if nextIsEnd:
                if ratingIndex is not None and nGames[ratingIndex] < gamesPerBand:
                    pgns[ratingIndex] += f'{pgn}\n'
                    nGames[ratingIndex] += 1
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


extractGamesByRating([1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800], 5000)
