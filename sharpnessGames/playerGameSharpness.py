import chess
from chess import engine, pgn, Board
import matplotlib.pyplot as plt
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
    startSharp = 0.468*0.5

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
                        csharp = functions.sharpnessLC0(c[0]) * ((1000-max(c[0]))/1000)
                    
                    diff = max(-3, min(3, float(csharp-lastSharp)))
                    lastSharp = csharp

                    if not node.turn():
                        sharp['white'].append((diff, move))
                    else:
                        sharp['black'].append((diff, move))
                        move += 1       # Counting here to have full moves
    return sharp


def sharpChangeForPlayer(pgnPaths: list(), player: str) -> list:
    """
    This function calculates the sharpness change per move for a given palyer
    pgnPaths: list
        The paths to the PGN files
    player: str
        Name of the player in searched for
    return -> list
        A list of tuples with the sharpness change and move number
    """
    startSharp = 0.468 * 0.55

    sharp = list()
    for pgnPath in pgnPaths:
        with open(pgnPath, 'r') as pgn:
            while game := chess.pgn.read_game(pgn):
                if player in game.headers['White']:
                    white = True
                elif player in game.headers['Black']:
                    white = False
                else:
                    print(f'Game skipped; players: {game.headers["White"]} - {game.headers["Black"]}')
                    break

                move = 1

                lastSharp = startSharp
                lastEval = 0.3
                node = game
                
                while not node.is_end():
                    node = node.variations[0]
                    if c := functions.readComment(node, True, True):
                        csharp = functions.sharpnessLC0(c[0]) * ((1000-max(c[0]))/1000)
                        if max(c[0]) >= 800:
                            csharp = 0
                        ceval = int(c[1])
                    else:
                        continue

                    sharpDiff = csharp-lastSharp

                    lastSharp = csharp
                    lastEval = ceval

                    if node.turn() != white:
                        sharp.append((max(-3, min(3, sharpDiff)), move, white))
                        move += 1
    return sharp


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


def plotGameSharpness(pgnPath: str, filename: str = None):
    """
    This function plots the sharpness change of a single game, move by move
    pgnPath: str
        Path to a PGN file that contains only 1 game
    """
    sharpChange = sharpChangeByColor([pgnPath], False)
    white = sharpChange['white']
    black = sharpChange['black']

    fig, ax = plt.subplots(figsize=(10,6))

    ax.plot(range(1, len(white)+1), [min(w[0], 5) for w in white], color='#f8a978', label='White sharpness change')
    ax.plot(range(1, len(black)+1), [min(b[0], 5) for b in black], color='#111111', label='Black sharpness change')

    plt.axhline(0, color='black', linewidth=0.5)
    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Move Number')
    ax.set_ylabel('Sharpness Change')
    ax.set_xlim(1, len(white)+1)
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotPlayerSharpness(sharpChange: list, filename: str = None):
    """
    This function plots the average sharpness change of a player per move for White and Black
    sharpChange: list
        List returned by sharpChangeForPlayer    
    """
    white = [(sc[0], sc[1]) for sc in sharpChange if sc[2]]
    black = [(sc[0], sc[1]) for sc in sharpChange if not sc[2]]

    maxWMoves = max([w[1] for w in white])
    wMoveAvg = [sum([w[0] for w in white if w[1] == move])/len([w[0] for w in white if w[1] == move]) for move in range(1, maxWMoves+1)]

    maxBMoves = max([b[1] for b in black])
    bMoveAvg = [sum([b[0] for b in black if b[1] == move])/len([b[0] for b in black if b[1] == move]) for move in range(1, maxBMoves+1)]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(range(1, len(wMoveAvg)+1), wMoveAvg, color='#f8a978')
    ax.plot(range(1, len(bMoveAvg)+1), bMoveAvg, color='#111111')
    plt.axhline(0, color='black', linewidth=0.5)
    
    ax.set_facecolor('#e6f7f2')
    ax.set_xlim(1, 40)
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def comparePlayerSharpness(sharpChanges: list, players: list, filename: str = None):
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#689bf2','#f8a978', '#7ed3b2', '#ff87ca', '#beadfa']

    for i, sc in enumerate(sharpChanges):
        maxMove = max([s[1] for s in sc])
        moveSharpAvg = [sum([s[0] for s in sc if s[1] == move])/len([s[0] for s in sc if s[1] == move]) for move in range(1, maxMove+1)]

        ax.plot(range(1, maxMove+1), moveSharpAvg, color=colors[i], label=players[i])

    plt.axhline(0, color='black', linewidth=0.5)
    ax.set_xlim(1, 40)
    ax.set_ylim(-0.05, 0.05)
    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Move Number')
    ax.set_ylabel('Sharpness Change')
    ax.legend()
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


if __name__ == '__main__':
    pgns = ['../out/games/tal-bot-sac.pgn']
    sharpChange = sharpChangeByColor(pgns)
    # print(sharpChange)
    # plotGameSharpness('../out/games/byrne-fisher.pgn')
    plotGameSharpness('../out/games/kasparov-topalov.pgn', '../out/kasparov-topalov_sharp.png')
    plotGameSharpness('../out/games/tal-bot-sac.pgn', '../out/tal-botvinnik_sharp.png')
    tal = ['../out/games/tal1959-1962-out.pgn']
    bot = ['../out/games/botvinnik1959-1962-out.pgn']
    scTal = sharpChangeForPlayer(tal, 'Tal, M')
    scBot = sharpChangeForPlayer(bot, 'Botvinnik')
    # plotPlayerSharpness(scTal)
    # plotPlayerSharpness(scBot)
    comparePlayerSharpness([scTal, scBot], ['Tal', 'Botvinnik'], '../out/tal-bot-players_sharp.png')
