import analysis
import tournamentReport
import chess
import os, sys
import matplotlib.pyplot as plt

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
    # sharpness seems to explode sometimes
    w = [min(s[0], 10) for s in sharpChange['white'] if not maxMove or s[1] <= maxMove]
    b = [min(s[0], 10) for s in sharpChange['black'] if not maxMove or s[1] <= maxMove]
    return (sum(w)/len(w), sum(b)/len(b))


def getClockTimes(pgnPaths: list) -> dict:
    """
    This function gets the clocktimes for each move for Black and White
    pgnPaths: list
        A list of PGN files which contain the clock times
    return -> dict
        A dictionary indexed by color and containing a list with the clocktimes and move number
    """
    clock = {'white': [], 'black': []}
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while (game := chess.pgn.read_game(pgn)):
                if int(float(game.headers['Round'])) % 2 == 1:
                    continue
                move = 1
                node = game
                while not node.is_end():
                    node = node.variations[0]
                    time = node.clock()
                    if not time:
                        break

                    if not node.turn():
                        clock['white'].append((time, move))
                    else:
                        clock['black'].append((time, move))
                        move += 1
    return clock


def getColorScore(pgnPaths: list) -> tuple:
    """
    This function returns the armageddon scores for each color
    pgnPaths: list
        The paths to the PGN files
    return -> tuple
        (whiteScore, blackScore)
    """
    nGames = 0
    white = 0
    black = 0
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                r = game.headers['Result']
                if r == '*' or int(float(game.headers['Round'])) % 2 == 1:
                    continue
                nGames += 1
                if r == '1-0':
                    white += 1
                else:
                    black += 1
    return (white/nGames, black/nGames)


def plotClockTimes(clockTimes: dict, filename: str = None) -> None:
    """
    This fucntions plots the average clock times for White and Black on each move
    clockTimes: dict
        Dictionary generated by getClockTimes
    filename: str
        The name of the file to which the plot will be saved.
        If no name is given, the plot will be shown instead.
    """
    wAvg = list()
    bAvg = list()
    for i in range(1, 150):
        white = [clock[0] for clock in clockTimes['white'] if clock[1] == i]
        black = [clock[0] for clock in clockTimes['black'] if clock[1] == i]
        if not white or not black:
            break
        wAvg.append(sum(white)/len(white))
        bAvg.append(sum(black)/len(black))

    fig, ax = plt.subplots(figsize=(10,6))

    ax.plot(range(len(wAvg)), wAvg, color='#f8a978', label='White clock time')
    ax.plot(range(len(bAvg)), bAvg, color='#111111', label='Black clock time')
    # ax.plot(range(len(wAvg)), [100*(wAvg[i]-bAvg[i])/bAvg[i] for i in range(len(wAvg))], label='White time advantage')

    ax.set_facecolor('#e6f7f2')
    ax.set_xlim(0, len(wAvg))
    ax.set_ylim(0, max(wAvg)+20)
    ax.set_xlabel('Move number')
    ax.set_ylabel('Clock time (in sec)')
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Average Clock Time')
    ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotSharpChange(pgnPaths: list, filename: str = None) -> None:
    """
    This function plots the average sharpness change per move for given PGN files
    pgnPaths: list
        The paths to the PGN files
    filename: str
        The name of the file to which the plot will be saved.
        If no name is given, the plot will be shown instead.
    """

    sharp = sharpChangeByColor(pgnPaths)
    maxMove = 40

    fig, ax = plt.subplots(figsize=(10,6))

    ax.plot(range(maxMove), [getAvgSharpChange(sharp, i)[0] for i in range(1, maxMove+1)], color='#f8a978', label='White sharpness change')
    ax.plot(range(maxMove), [getAvgSharpChange(sharp, i)[1] for i in range(1, maxMove+1)], color='#111111', label='Black sharpness change')
    plt.axhline(0, color='black', linewidth=0.5)

    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Move number')
    ax.set_ylabel('Sharpness Change')
    ax.set_xlim(0, maxMove)
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Average Sharpness Change per Move')
    ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotScores(scores: dict, filename: str = None) -> None:
    """
    This functions plots the normalised scores for classical and armageddon games
    filename: str
        The name of the file to which the plot will be saved.
        If no name is given, the plot will be shown instead.
    """
    normScores = dict()
    for p, s in scores.items():
        normScores[p] = [s[0][0]/s[0][1], s[1][0]/s[1][1]]
    tournamentReport.plotBarChart(normScores, ['Classical Score', 'Armageddon Score'], 'Scores', 'Score', short={'Nepomniachtchi': 'Nepo', 'Vachier-Lagrave': 'MVL'}, filename=filename)


if __name__ == '__main__':
    norway = ['../out/games/Norway2021-out.pgn', '../out/games/Norway2022-out.pgn', '../out/games/Norway2023-out.pgn',  '../out/games/Norway2024-out.pgn']
    n2 = ['../resources/Norway2021.pgn', '../resources/Norway2022.pgn', '../resources/Norway2023.pgn', '../resources/Norway2024.pgn']
    SC = sharpChangeByColor(norway)
    print(getAvgSharpChange(SC))
    for i in [5, 10, 15, 20, 25]:
        print(i, getAvgSharpChange(SC, i))
    scores = compareScores(norway)
    # plotScores(scores, '../out/armScores.png')
    times = getClockTimes(n2)
    plotClockTimes(times)
    # print(getColorScore(norway))
    # plotSharpChange(norway, '../out/armSharp.png')
