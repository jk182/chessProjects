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
                    
                    diff = float(csharp-lastSharp)
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
    startSharp = 0.468

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
                node = game
                
                while not node.is_end():
                    node = node.variations[0]
                    if c := functions.readComment(node, True, True):
                        csharp = functions.sharpnessLC0(c[0])
                    else:
                        continue

                    sharpDiff = cshapr-lastSharp
                    lastSharp = csharp

                    if node.turn() != white:
                        sharp.append((diff, move))
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


def plotGameSharpness(pgnPath: str):
    """
    This function plots the sharpness change of a single game, move by move
    pgnPath: str
        Path to a PGN file that contains only 1 game
    """
    sharpChange = sharpChangeByColor([pgnPath], False)
    white = sharpChange['white']
    black = sharpChange['black']

    fig, ax = plt.subplots(figsize=(10,6))

    ax.plot(range(len(white)), [min(w[0], 5) for w in white], color='#f8a978', label='White sharpness change')
    ax.plot(range(len(black)), [min(b[0], 5) for b in black], color='#111111', label='Black sharpness change')

    ax.set_facecolor('#e6f7f2')
    ax.set_xlabel('Move Number')
    ax.set_ylabel('Sharpness Change')
    ax.set_xlim(0, len(white))
    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)

    ax.legend()

    plt.show()


if __name__ == '__main__':
    pgns = ['../out/games/Norway2023-out.pgn']
    sharpChange = sharpChangeByColor(pgns)
    # print(sharpChange)
    plotGameSharpness('../resources/tal-smyslov.pgn')
