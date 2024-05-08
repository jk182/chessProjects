# Future Idea: calculate how much a player narrows the known moves
import os, sys
import subprocess
import chess
import re
import pickle
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import evalDB


def searchPositions(pgn: str, script: str, db: str) -> tuple:
    """
    Going through each game of a PGN and finding the novelties.
    pgn: str
        Path to the PGN file
    script: str
        Path to the SCID-script which looks if the position is new
    db: str
        Path to the SCID-database to compare the game to
    return -> tuple
        Tuple containing dictionaries with the novelties and book moves
    """
    novelties = dict()
    # dictionary to count the book moves, values are lists with the number of moves with more than 10000, 1000, 100, 10, 1 games
    bookMoves = dict()
    cache = dict()
    gameNR = 1
    with open(pgn, 'r') as tournament:
        while (game := chess.pgn.read_game(tournament)):
            print(f'Starting with game {gameNR}')
            gameNR += 1

            white = game.headers["White"]
            black = game.headers["Black"]
            board = game.board()

            print(white, black)

            for move in game.mainline_moves():
                posBefore = board.fen()
                board.push(move)
                posAfter = board.fen()
                
                if posAfter in cache.keys():
                    numGames = cache[posAfter]
                else:
                    search = str(subprocess.run(['tkscid', script, db, posAfter], stdout=subprocess.PIPE).stdout)
                    numGames = gamesFromSearchOutput(search)
                    cache[posAfter] = numGames

                if board.turn:
                    player = black
                else:
                    player = white
                if numGames > 1:
                    if player not in bookMoves.keys():
                        bookMoves[player] = [0, 0, 0, 0, 0]
                    if numGames > 10000:
                        start = 0
                    elif numGames > 1000:
                        start = 1
                    elif numGames > 100:
                        start = 2
                    elif numGames > 10:
                        start = 3
                    else:
                        start = 4
                    for i in range(start, len(bookMoves[player])):
                        bookMoves[player][i] += 1
                    continue

                if not isMistake(posBefore, posAfter):
                    if player not in novelties.keys():
                        novelties[player] = 1
                    else:
                        novelties[player] += 1
                    print(f'Novelty: {move}')
                break
    return (novelties, bookMoves)



def gamesFromSearchOutput(output: str) -> int:
    """
    This function takes the output from a SCID search and extracts the number of games
    output: str
        The unformatted output
    return -> int
        The number of games found
    """
    games = re.findall('\d+', output)[0]
    return int(games)


def isMistake(posBefore: str, posAfter: str, mistakeThreshold: int = 70) -> bool:
    """
    This function takes the position before and after a move and determines if the move was a mistake
    posBefore: str
        FEN string of the position before the move
    posAfter: str
        FEN string of the position after the move
    mistakeThreshold: int
        Centipawn loss which counts as a mistake
    return -> bool:
        True if the move was a mistake, False otherwise
    """
    sf = functions.configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    time = 3
    # if evalDB.contains(posBefore):
    if False:
        cpBefore = int(evalDB.getEval(posBefore, False))
    else:
        info = sf.analyse(chess.Board(posBefore), chess.engine.Limit(time=time))
        cpBefore = info['score'].white().score()
        # TODO: enter positions into eval DB
    # if evalDB.contains(posAfter):
    if False:
        cpAfter = int(evalDB.getEval(posAfter, False))
    else:
        info = sf.analyse(chess.Board(posAfter), chess.engine.Limit(time=time))
        cpAfter = info['score'].white().score()
        # TODO: enter positions into eval DB
    sf.quit()
    return abs(cpBefore-cpAfter) > mistakeThreshold


def sortPlayers(d: dict, index: int) -> list:
    """
    This function takes a dictionary with a list as values and sorts the keys by the value at the index of the list
    """

    players = list()
    for i in range(len(d.keys())):
        maximum = -1
        for k, v in d.items():
            if k in players:
                continue
            if isinstance(v, int):
                curr = v
            else:
                curr = v[index]
            if curr > maximum:
                p = k
                maximum = curr
        players.append(p)
    return players


def plotNovelties(novelties: dict, short: dict = None, filename: str = None):
    """
    This function plots the number of novelties per player
    novelties: dict
        A dictionary index by the players and the number of novelties as values
    short: dict
        Short names for the players to replace them in the graph
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved
    """
    sort = sortPlayers(novelties, 0)
    labels = list()
    for i, player in enumerate(sort):
        p = player.split(',')[0]
        if short:
            if p in short.keys():
                p = short[p]
        labels.append(p)

    fig, ax = plt.subplots(figsize=(10,6))

    ax.set_facecolor('#e6f7f2')
    plt.xticks(rotation=90)
    plt.yticks(range(0,9))
    plt.xticks(ticks=range(1, len(sort)+1), labels=labels)

    ax.bar([i+1 for i in range(len(sort))], [ novelties[p] for p in sort], color='#689bf2', edgecolor='black', linewidth=0.5, width=0.5, label='Novelties')
    ax.legend()
    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.1, right=0.95)
    plt.title('Number of novelties')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def plotBookMoves(bookMoves: dict, short: dict = None, filename: str = None, nGames: int = 14):
    """
    This function plots the number of book moves per player
    bookMoves: dict
        A dictionary index by the players and the number of book moves as values
    short: dict
        Short names for the players to replace them in the graph
    filename: str
        The name of the file to which the graph should be saved.
        If no name is specified, the graph will be shown instead of saved
    nGames: int
        The number of games per player
    """
    sort = sortPlayers(bookMoves, 0)
    labels = list()
    for i, player in enumerate(sort):
        p = player.split(',')[0]
        if short:
            if p in short.keys():
                p = short[p]
        labels.append(p)

    fig, ax = plt.subplots(figsize=(10,6))

    ax.set_facecolor('#e6f7f2')
    plt.xticks(rotation=90)
    plt.xticks(ticks=range(1, len(sort)+1), labels=labels)
    plt.ylim(0, 11.5)
    
    values = list(bookMoves.values())
    width = 1 / (2*len(values[0]))
    offset = -width*(len(values[0])-0.5)/2

    legendNames = ['>10,000 games', '>1,000 games', '>100 games', '>10 games', '>1 game']
    colors = ['#689bf2', '#7ed3b2', '#ff87ca', '#beadfa', '#f8a978']

    for i in range(len(values[0])):
        ax.bar([j+1+offset for j in range(len(sort))], [bookMoves[p][i]/nGames for p in sort], width=width, label=legendNames[i], color=colors[i], edgecolor='black', linewidth=0.5)
        offset += width

    ax.legend(loc='upper center', ncol=5)
    fig.subplots_adjust(bottom=0.2, top=0.95, left=0.1, right=0.95)
    plt.title('Number of book moves')
    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()



if __name__ == '__main__':
    db = '/home/julian/chess/database/gameDB/novelties'
    player = 'Carlsen, M.'
    script = 'searchPosition.tcl'
    pgn = '../out/candidates2024-WDL+CP.pgn'
    fen = 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6'

    # o = subprocess.run(['tkscid', script, db, fen], stdout=subprocess.PIPE).stdout
    # print(o)
    # print(gamesFromSearchOutput(str(o)))
    """
    nov, book = searchPositions(pgn, script, db)
    print(nov, book)
    with open(f'../out/candidates-novelties.pkl', 'wb+') as f:
        pickle.dump(nov, f)
    with open(f'../out/candidates-bookMoves.pkl', 'wb+') as f:
        pickle.dump(book, f)
    """
    with open(f'../out/candidates-novelties.pkl', 'rb+') as f:
        novelties = pickle.load(f)
    nicknames = {'Nepomniachtchi': 'Nepo', 'Praggnanandhaa R': 'Pragg'}
    with open(f'../out/candidates-bookMoves.pkl', 'rb+') as f:
        bookMoves = pickle.load(f)
    # plotNovelties(novelties, short=nicknames)
    plotBookMoves(bookMoves, short=nicknames)
