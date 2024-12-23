import chess
import os, sys
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import plotly.graph_objects as go


def getMoveSituation(pgnPath: str) -> dict:
    """
    This gets the number of moves where each player was much better, better, equal, worse and much worse
    pgnPath: str
        The path to the PGN file of the match
    """
    player1 = None
    player2 = None
    moves = dict()

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if not player1:
                player1 = game.headers['White']
                player2 = game.headers['Black']
                moves[player1] = [0] * 6
                moves[player2] = [0] * 6
            w = game.headers['White']
            b = game.headers['Black']
            node = game

            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = functions.readComment(node, True, True)[1]
                    if not node.turn():
                        moves[w][0] += 1
                        if cp > 100:
                            moves[w][1] += 1
                        elif cp >= 50:
                            moves[w][2] += 1
                        elif cp >= -50:
                            moves[w][3] += 1
                        elif cp > -100:
                            moves[w][4] += 1
                        else:
                            moves[w][5] += 1
                    else:
                        moves[b][0] += 1
                        if cp > 100:
                            moves[b][5] += 1
                        elif cp >= 50:
                            moves[b][4] += 1
                        elif cp >= -50:
                            moves[b][3] += 1
                        elif cp > -100:
                            moves[b][2] += 1
                        else:
                            moves[b][1] += 1
    return moves


def getBetterGames(pgnPath: str) -> list:
    """
    This function gets the number of better and won games for each player
    pgnPath: str
        The path to the PGN file of the match
    return -> list
        A list containing the better and won games for each player
    """
    better = [[0, 0], [0, 0]]
    firstPlayer = None
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            r = game.headers["Result"]
            if not firstPlayer:
                firstPlayer = game.headers["White"]
            if firstPlayer == game.headers["White"]:
                index = 0
                if r == '1-0':
                    better[0][1] += 1
                elif r == '0-1':
                    better[1][1] += 1
            else:
                index = 1
                if r == '0-1':
                    better[0][1] += 1
                elif r == '1-0':
                    better[1][1] += 1

            node = game
            rec = [False, False]
            
            while not node.is_end():
                if rec == [True, True]:
                    break
                node = node.variations[0]
                if node.comment:
                    cp = functions.readComment(node, True, True)[1]
                    if cp < -100 and not rec[0]:
                        rec[0] = True
                        better[(index+1)%2][0] += 1
                    elif cp > 100 and not rec[1]:
                        rec[1] = True
                        better[index][0] += 1
    return better


def getClockTimes(pgnPath: str) -> list:
    """
    This function reads the times from a PGN file with time stamps
    """
    times = [list(), list()]
    firstPlayer = None

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if firstPlayer is None:
                firstPlayer = game.headers["White"]
            node = game
            c = [list(), list()]
            while not node.is_end():
                node = node.variations[0]
                time = int(node.clock())
                if not time:
                    break
                if not node.turn():
                    c[0].append(time)
                else:
                    c[1].append(time)

            if game.headers["White"] == firstPlayer:
                times[0].append(c[0])
                times[1].append(c[1])
            else:
                times[0].append(c[1])
                times[1].append(c[0])
    return times


def getSharpChange(pgnPath: str) -> list:
    """
    This function calculates the sharpness change for the players.
    pgnPath: str
        The path to the PGN file of the match
    return -> list
        The sharpness change for each player. Each list contains a list for each game with the sharpness change for each move.
    """
    startSharp = 0.468 * 0.55
    sharpChange = [list(), list()]
    firstPlayer = None
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            sc1 = list()
            sc2 = list()
            if firstPlayer is None:
                firstPlayer = game.headers["White"]
            lastSharp = startSharp
            node = game

            while not node.is_end():
                node = node.variations[0]
                if c := functions.readComment(node, True, True):
                    sharp = functions.sharpnessLC0(c[0]) * ((1000-max(c[0]))/1000)
                    if max(c[0]) >= 800:
                        sharp = 0
                else:
                    continue
                sharpDiff = float(sharp-lastSharp)
                if node.turn():
                    if game.headers["Black"] == firstPlayer:
                        sc1.append(sharpDiff)
                    else:
                        sc2.append(sharpDiff)
                else:
                    if game.headers["White"] == firstPlayer:
                        sc1.append(sharpDiff)
                    else:
                        sc2.append(sharpDiff)
                lastSharp = sharp
            sharpChange[0].append(sc1)
            sharpChange[1].append(sc2)
    return sharpChange


def getInaccMistakesBlunders(pgnPath: str) -> list:
    """
    This gets the number of inaccuaracies, mistakes and blunders for each player.
    pgnPath: str
        Path to the PGN file containing all match games
    return -> list
        A list containing  a list with the numbers of inaccuracies, mistakes and blunders for each player
    """
    data = [[0]*3, [0]*3]
    bounds = (10, 15, 20)
    firstP = None
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if not firstP:
                firstP = game.headers["White"]

            node = game
            cpB = None
            
            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cpA = functions.readComment(node, True, True)[1]
                    if cpB is None:
                        cpB = cpA
                        continue
                    if node.turn():
                        wpB = functions.winP(cpB * -1)
                        wpA = functions.winP(cpA * -1)
                        if game.headers["Black"] == firstP:
                            index = 0
                        else:
                            index = 1
                    else:
                        wpB = functions.winP(cpB)
                        wpA = functions.winP(cpA)
                        if game.headers["White"] == firstP:
                            index = 0
                        else:
                            index = 1
                    diff = -wpA + wpB
                    if diff > bounds[2]:
                        data[index][2] += 1
                    elif diff > bounds[1]:
                        data[index][1] += 1
                    elif diff > bounds[0]:
                        data[index][0] += 1
                    cpB = cpA
    return data


def getOpeningMoves(pgnPath: str, maxPly: int = 10) -> list:
    """
    This function gets the opening moves and positions after these moves for each player
    """
    openings = [list(), list()]
    firstPlayer = None
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if firstPlayer is None:
                firstPlayer = game.headers["White"]
            board = game.board()
            opening = list()
            for i, move in enumerate(game.mainline_moves()):
                if i >= maxPly:
                    break
                oldBoard = board.copy()
                board.push(move)
                opening.append((board.fen(), oldBoard.variation_san([move]))) # variation_san gives also the move numbers
            if firstPlayer == game.headers["White"]:
                openings[0].append(opening)
            else:
                openings[1].append(opening)
    return openings


def getAccuracies(pgnPath: str) -> list:
    """
    This function gets the accuracies for each player
    pgnPath: str
        The path to the PGN file of the match
    return -> list
        A list containing a list of the accuracies for each player
    """
    accuracies = [list(), list()]
    firstPlayer = None

    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            if not firstPlayer:
                firstPlayer = game.headers["White"]
            node = game
            lastWP = None

            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = functions.readComment(node, True, True)[1]
                    wp = functions.winP(cp)
                    if lastWP is None:
                        lastWP = wp
                        continue
                    if node.turn():
                        acc = min(100, functions.accuracy(wp, lastWP))
                        if game.headers["Black"] == firstPlayer:
                            index = 0
                        else:
                            index = 1
                    else:
                        acc = min(100, functions.accuracy(lastWP, wp))
                        if game.headers["White"] == firstPlayer:
                            index = 0
                        else:
                            index = 1
                    accuracies[index].append(float(acc))
                    lastWP = wp
    return accuracies


def plotAccuracyDistribution(data: list, players: list, filename: str = None):
    """
    This method plots the accuracy distribution given the accuracy data
    data: list
        The path to the PGN file
    players: list
        The name of the players
    filename: str
        Filename of the plot if it should be saved instead of shown
    """
    colors = ['#689bf2', '#f8a978']
    acd = [dict(), dict()]
    for i in range(len(data)):
        for acc in data[i]:
            a = round(acc)
            a = max(a, 41)
            if a in acd[i].keys():
                acd[i][a] += 1
            else:
                acd[i][a] = 1

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_yscale("log")
    ax.set_facecolor('#e6f7f2')

    for i, accDis in enumerate(acd):
        xy = [ (k,v) for k,v in accDis.items() if k <= 100]
        nMoves = sum(accDis.values())
        ax.bar([x[0]-0.75+0.5*i for x in xy], [y[1]/nMoves for y in xy], width=0.5, color=colors[i], edgecolor='black', linewidth=0.5, label=players[i])

    plt.xlim(40, 100)
    ax.invert_xaxis()
    ax.set_xlabel('Move Accuracy')
    ax.set_ylabel('Relative number of moves')
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.15, right=0.95)
    # plt.title(f'Accuracy per move: {p}')
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
    ax.yaxis.get_major_formatter().set_scientific(False)
    ax.legend()
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(outFile, dpi=500)
    else:
        plt.show()


def plotBarChart(data: list, playerNames: list, ylabel: str, title: str, legend: list, colors: list = None, filename: str = None):
    """
    A general function to create bar charts
    data is assumed to be a list of lists. The first list is the data for the first player, the second one for the second player.
    """
    if not colors:
        colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    plt.xticks(ticks=range(1, len(data)+1), labels=playerNames)
    ax.set_ylabel(ylabel)

    nBars = len(data[0])
    width = 0.8/nBars
    offset = width * (1/2 - nBars/2)

    for j in range(nBars):
        ax.bar([i+1+offset+(width*j) for i in range(len(data))], [d[j] for d in data], color=colors[j%len(colors)], edgecolor='black', linewidth=0.5, width=width, label=legend[j])

    ax.legend()
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotMoveSituation(moveData: dict):
    """
    This function plots the number of better, equal and worse moves from getMoveSituation
    moveData: dict
        The dictionary returned by getMoveSituation
    """
    colors = ['#4ba35a', '#9CF196', '#F0EBE3', '#F69E7B', '#EF4B4B']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')

    player, m = list(moveData.items())[0]
    player = player.split(',')[0]
    bottom = 0
    factor = 1/m[0]
    for i in range(len(m)-1, 0, -1):
        ax.barh(player, m[i]*factor, left=bottom, color=colors[i-1], edgecolor='black', linewidth=0.2)
        bottom += m[i]*factor
    ax.set_xlim(0, 1)
    y2 = ax.twinx()
    y2.set_ylim(ax.get_ylim())
    y2.set_yticks([0])
    y2.set_yticklabels([list(moveData.keys())[1].split(',')[0]])

    plt.title('Number of moves where the players were better, equal or worse')
    plt.show()


def plotAvgLinePlot(data: list, playerNames: list, ylabel: str, title: str, legend: list, colors: list = None, maxMoves: int = 40, filename: str = None):
    """
    This function plots the average values of move data
    """
    if not colors:
        colors = ['#689bf2', '#5afa8d', '#f8a978', '#fa5a5a']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    
    for k, d in enumerate(data):
        avg = list()
        for i in range(maxMoves):
            l = [c[i] for c in d if len(c) > i]
            avg.append(sum(l)/len(l))
        ax.plot(range(1, maxMoves+1), avg, color=colors[k], label=legend[k])
    
    plt.xlim(1, maxMoves)
    ax.legend()
    plt.title(title)
    plt.axhline(0, color='black', linewidth=0.5)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


def plotOpeningDiagram(openings: list):
    positions = dict()
    moves = dict()
    for opening in openings:
        for i, o in enumerate(opening):
            if o[0] not in positions.keys():
                positions[o[0]] = o[1]
            elif positions[o[0]] != o[1]:
                print('Transposition')
            if i < len(opening)-1:
                k = (o[0], o[1], opening[i+1][0], opening[i+1][1])
                if k not in moves.keys():
                    moves[k] = 1
                else:
                    moves[k] += 1
    items = list(positions.items())
    labels = [i[1] for i in items]
    link = dict(source=list(), target=list(), value=list())
    for k, v in moves.items():
        link['source'].append(items.index((k[0], k[1])))
        link['target'].append(items.index((k[2], k[3])))
        link['value'].append(v)
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = labels,
          color = "blue"
        ),
        link = link
      )])

    fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
    fig.show()
    

if __name__ == '__main__':
    pgn = '../out/games/ding-gukesh-out.pgn'
    # moveSituation = getMoveSituation(pgn)
    # plotMoveSituation(moveSituation)
    players = ["Gukesh", "Ding"]
    imb = getInaccMistakesBlunders(pgn)
    # plotBarChart(imb, players, "Number of inaccuracies, mistakes, blunders", "Number of inaccuracies, mistakes and blunders", ["Inaccuracies", "Mistakes", "Blunders"])
    acc = getAccuracies(pgn)
    # plotAccuracyDistribution(acc, players)
    better = getBetterGames(pgn)
    # plotBarChart(better, players, "Number of games", "Number of better and won games", ["Better games", "Won games"])
    sc = getSharpChange(pgn)
    # plotAvgLinePlot(sc, players, "Average sharpness change per move", "Average sharpness change per move", ["Gukesh sharpness change", "Ding sharpness change"])
    clocks = getClockTimes('../resources/ding-gukesh-clocks.pgn')
    print(clocks)
    openings = getOpeningMoves(pgn, maxPly = 8)
    plotOpeningDiagram(openings[0])
