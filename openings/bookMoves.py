import chess
import chess.pgn
import subprocess


def getPlayerTimes(game: chess.pgn.Game, startTime: int = 5430, increment: int = 30) -> list:
    """
    This function extracts the clock times for each player from a chess.Game object
    startTime: int
        The time at the start of the game in seconds
    return -> list
        [[wTimeBeforeMove1, wTimeBeforeMove2, ...], [bTimeBeforeMove1, ...]]
    """
    wTime = [startTime]
    bTime = [startTime]

    node = game
    while not node.is_end():
        node = node.variations[0]

        if not node.turn():
            if node.clock() is None:
                time = wTime[-1] + increment # if no time is given, I assume that the move was played instantly
            else:
                time = int(node.clock())

            wTime.append(time)
        else:
            if node.clock() is None:
                time = bTime[-1] + increment
            else:
                time = int(node.clock())
            bTime.append(time)
    return [wTime, bTime]


def getNumberOfGamesBeforeEachMove(game: chess.pgn.Game, script: str, db: str) -> list:
    """
    This function gets the number of games in the database before each move in the game
    game: chess.Game
        The given game
    script: str
        Path to the tkscid script to get the number of games in the database
    db: str
        Path to the SCID database
    return -> list
        [nGamesBeforeMove1, nGamesBeforeMove2, ...]
    """
    nGames = list()

    board = game.board()
    date = game.headers["Date"]
    for move in game.mainline_moves():
        n = int(subprocess.run(['tkscid', script, db, board.fen(), date], stdout=subprocess.PIPE, text=True).stdout.strip())
        nGames.append(n)
        if n == 0:
            break
        board.push(move)

    return nGames





def getBookMoves(pgnPath: str, script: str, db: str, startTime: int = 5430, increment: int = 30):
    """
    """
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            clockTimes = getPlayerTimes(game, startTime, increment)
            nGames = getNumberOfGamesBeforeEachMove(game, script, db)

            print(clockTimes)
            print(nGames)


if __name__ == '__main__':
    db = '/Users/julian/Library/Mobile Documents/com~apple~CloudDocs/chessDB'
    script = 'searchPosition.tcl'
    pgn = '../resources/vanForeest-gukesh.pgn'
    getBookMoves(pgn, script, db)
