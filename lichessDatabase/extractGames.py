import chess
import chess.pgn
import io


def extractGamesByRating(ratingBands: list, gamesPerBand: int, maxRatingDiff: int = 50):
    pgns = list()
    pgns = [""] * len(ratingBands)
    nextIsEnd = False
    pgn = ""
    wElo = None
    bElo = None
    ratingIndex = None

    for i in range(1000):
        line = input()
        pgn = f'{pgn}{line.strip()}\n'
        if "WhiteElo" in line:
            wElo = int(line.split('"')[1])
        if "BlackElo" in line:
            bElo = int(line.split('"')[1])
            if abs(wElo-bElo) <= maxRatingDiff and (wElo+bElo)/2 >= ratingBands[0]:
                ratingIndex = len(ratingBands)-1
                for i in range(len(ratingBands)-1):
                    if ratingBands[i] <= (wElo+bElo)/2 < ratingBands[i+1]:
                        ratingIndex = i
                        break
            else:
                ratingIndex = None
        if not line.strip():
            if nextIsEnd:
                if ratingIndex is not None:
                    pgns[ratingIndex] += f'{pgn}\n'
                pgn = ""
                nextIsEnd = False
            else:
                nextIsEnd = True

    for p in pgns:
        f = io.StringIO(p)
        while game := chess.pgn.read_game(f):
            print(game)
    return pgns


extractGamesByRating([1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800], 1000)
