import chess
from chess import pgn


def getScoresForRatings(pgnPaths: list) -> dict:
    """
    This calculates the scores in the PGNs for a given rating against each opponent rating band
    """
    results = dict()
    ratingBands = list(range(2500, 3000, 50))
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if "WhiteElo" not in game.headers.keys() or "BlackElo" not in game.headers.keys():
                    print("No Elo")
                    continue
                wElo = int(game.headers['WhiteElo'])
                bElo = int(game.headers['BlackElo'])
                if wElo < min(ratingBands) or bElo < min(ratingBands):
                    continue
                for i, rating in enumerate(ratingBands):
                    if rating > wElo:
                        wEloBand = ratingBands[i-1]
                        break
                for i, rating in enumerate(ratingBands):
                    if rating > bElo:
                        bEloBand = ratingBands[i-1]
                        break
                result = game.headers['Result']
                if result == '1-0':
                    wPoints = 1
                    bPoints = 0
                elif result == '1/2-1/2':
                    wPoints = 0.5
                    bPoints = 0.5
                elif result == '0-1':
                    wPoints = 0
                    bPoints = 1
                else:
                    print(f'Result not found: {result}')
                    continue

                if wEloBand in results.keys():
                    if bEloBand in results[wEloBand].keys():
                        results[wEloBand][bEloBand][0] += wPoints
                        results[wEloBand][bEloBand][1] += 1
                    else:
                        results[wEloBand][bEloBand] = [wPoints, 1]
                else:
                    results[wEloBand] = dict()
                    results[wEloBand][bEloBand] = [wPoints, 1]
                if bEloBand in results.keys():
                    if wEloBand in results[bEloBand].keys():
                        results[bEloBand][wEloBand][0] += bPoints
                        results[bEloBand][wEloBand][1] += 1
                    else:
                        results[bEloBand][wEloBand] = [bPoints, 1]
                else:
                    results[bEloBand] = dict()
                    results[bEloBand][wEloBand] = [bPoints, 1]
    ret = dict()
    for k, v in results.items():
        ret[k] = dict()
        for k2, v2 in v.items():
            ret[k][k2] = round(v2[0]/v2[1], 2)
    return ret


if __name__ == '__main__':
    blitz = ['../resources/worldBlitz2023.pgn', '../resources/worldBlitz2024.pgn', '../resources/worldBlitz2022.pgn', '../resources/teamBlitz2025.pgn']
    ratingScores = getScoresForRatings(blitz)
    for k, v in ratingScores.items():
        print(k, v)

