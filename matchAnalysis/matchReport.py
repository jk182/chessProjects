import chess
import os, sys
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


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


if __name__ == '__main__':
    pgn = '../out/games/wcc2023-out.pgn'
    moveSituation = getMoveSituation(pgn)
    plotMoveSituation(moveSituation)
