import chess
import chess.pgn

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
from gameStatistics import gameAccuracy


def getAccuraciesByYear(pgnPath: str, player: str, lichessAnalysis: bool = False) -> dict:
    """
    This gets the accuracies of a player and his opponents from a PGN file
    pgnPath: str
        Path to the PGN file
    player: str
        Name of the player
    lichessAnalysis: bool
        If this is true, the PGN file is assumed to have been analysed by Lichess
    return -> dict:
        {year: [(playerAccGame1, oppAccGame1), (playerAccGame2, oppAccGame2), ...], ...}
    """
    accData = dict()
    startEval = 20
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if player in game.headers["White"]:
                white = True
            elif player in game.headers["Black"]:
                white = False
            else:
                print(f'Player {player} not found in {game.headers["White"]}-{game.headers["Black"]}')

            year = int(game.headers["Date"].split('.')[0])

            if year not in accData:
                accData[year] = list()

            evals = [startEval]

            node = game
            while not node.is_end():
                node = node.variations[0]
                if lichessAnalysis:
                    if node.eval():
                        cp = int(node.eval().white().score(mate_score=10000))
                    else:
                        print('No evaluation found')
                else:
                    if not functions.readComment(node, True, True):
                        print('No evaluation found')
                    else:
                        cp = functions.readComment(node, True, True)[1]

                evals.append(cp)

            axsl = gameAccuracy.calculateGeneralisedMean(evals)
            if white:
                playerAcc = functions.gameAccuracy(axsl[0])
                oppAcc = functions.gameAccuracy(axsl[1])
            else:
                playerAcc = functions.gameAccuracy(axsl[1])
                oppAcc = functions.gameAccuracy(axsl[0])

            accData[year].append((playerAcc, oppAcc))

    return accData


if __name__ == '__main__':
    pgn = '../out/carlsenClassicalAnalysed.pgn'
    accData = getAccuraciesByYear(pgn, 'Carlsen')
    pgn = '../out/capablancaTournamentGames_analysed.pgn'
    accData = getAccuraciesByYear(pgn, 'Capablanca')
    for k, v in accData.items():
        p = sum([x[0] for x in v])/len(v)
        o = sum([x[1] for x in v])/len(v)
        print(k, round(p, 2), round(o, 2), round(p-o, 2))

    for i in range(2):
        total = sum([sum([x[i] for x in v])/len(v) for v in accData.values()]) / len(accData)
        print(round(total, 3))
