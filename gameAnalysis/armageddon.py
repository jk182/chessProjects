import analysis
import tournamentReport
import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def sharpChangeByColor(pgnPaths: list(), onlyArm: bool = True) -> dict:
    """
    This function calculates the sharpness change per move for each color in a list of PGN files.
    pgnPaths: list
        The paths to the PGN files
    onlyArm: bool
        This specifies if only armageddon games should be looked at
    return -> dict
        A dictionary indexed by color and containing a list of tuples containing the sharpness change and the move number
    """
    startSharp = 0.468

    sharp = {'white': list(), 'black': list()}
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while (game := chess.pgn.read_game(pgn)):
                if onlyArm:
                    if int(float(game.headers['Round'])) % 2 == 1:      # In all PGNs, the armageddon games are the games in even rounds
                        continue
                move = 1

                node = game
                lastSharp = startSharp
                
                while not node.is_end():
                    node = node.variations[0]
                    if c := functions.readComment(node, True, True):
                        csharp = functions.sharpnessLC0(c[0])
                    
                    diff = csharp-lastSharp
                    lastSharp = csharp

                    if not node.turn():
                        sharp['white'].append((diff, move))
                    else:
                        sharp['black'].append((diff, move))
                        move += 1       # Counting here to have full moves
    return sharp


def compareScores(pgnPaths: list) -> dict:
    """
    This function calculates the scores of the players in classical and armageddon chess.
    It is assumed that the even numbered rounds are the rounds with the armageddon games.
    pgnPaths: list
        A list with all paths to PGN files to consider
    return -> dict
        Dictonary indexed by players containing a list: [[clasPoints, clasGames], [armPoints, armGames]]
    """
    scores = dict()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while (game := chess.pgn.read_game(pgn)):
                if 'Result' not in game.headers.keys() or game.headers['Result'] == '*':
                    continue

                white = game.headers['White']
                black = game.headers['Black']
                for p in [white, black]:
                    if p not in scores.keys():
                        scores[p] = [[0, 0], [0, 0]]

                result = game.headers['Result']

                if int(float(game.headers['Round'])) % 2 == 0:
                    scores[white][1][1] += 1
                    scores[black][1][1] += 1
                    if result == '1-0':
                        scores[white][1][0] += 1
                    else:
                        scores[black][1][0] += 1
                else:
                    scores[white][0][1] += 1
                    scores[black][0][1] += 1
                    if result == '1-0':
                        scores[white][0][0] += 1
                    elif result == '0-1':
                        scores[black][0][0] += 1
                    else:
                        scores[white][0][0] += 0.5
                        scores[black][0][0] += 0.5
    return scores


def getAvgSharpChange(sharpChange: dict, maxMove: int = None) -> tuple:
    """
    This function calculates the average sharpness change for White and Black up to a given move to be able to look at openings.
    sharpChange: dict
        The dictionary returned by sharpChangeByColor
    maxMove: int
        The maximum move number to look at.
        If no value is specified, all moves will be considered
    return -> tuple
        Average sharpness change per move for White and Black
    """
    w = [s[0] for s in sharpChange['white'] if not maxMove or s[1] <= maxMove]
    b = [s[0] for s in sharpChange['black'] if not maxMove or s[1] <= maxMove]
    return (sum(w)/len(w), sum(b)/len(b))


def plotScores(scores: dict) -> None:
    """
    This functions plots the normalised scores for classical and armageddon games
    """
    normScores = dict()
    for p, s in scores.items():
        normScores[p] = [s[0][0]/s[0][1], s[1][0]/s[1][1]]
    tournamentReport.plotBarChart(normScores, ['Classical Score', 'Armageddon Score'], 'Scores', 'Score')


if __name__ == '__main__':
    norway = ['../out/games/Norway2021-out.pgn', '../out/games/Norway2022-out.pgn', '../out/games/Norway2023-out.pgn',  '../out/games/Norway2023-out.pgn']
    SC = sharpChangeByColor(norway)
    print(getAvgSharpChange(SC))
    for i in [5, 10, 15, 20, 25]:
        print(i, getAvgSharpChange(SC, i))
    scores = compareScores(norway)
    plotScores(scores)
