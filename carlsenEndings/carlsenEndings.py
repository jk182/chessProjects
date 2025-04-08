import chess
from chess import pgn


def getEqualEndgameScore(pgnPath: str):
    totalGames = 0
    blitzGames = 0
    rapidGames = 0
    chess960Games = 0
    endings = 0
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            totalGames += 1
            event = game.headers['Event']
            if 'blitz' in event.lower():
                blitzGames += 1
            elif 'rapid' in event.lower():
                rapidGames += 1
            elif 'freestlye' in event.lower() or 'fischer random' in event.lower():
                chess960Games += 1
            else:
                board = chess.Board()
                for move in game.mainline_moves():
                    board.push(move)
                    if isEndgame(board):
                        endings += 1
                        break
    print(totalGames)
    print(blitzGames)
    print(rapidGames)
    print(chess960Games)
    print(endings)


def isEndgame(position: chess.Board) -> bool:
    """
    This function determins if a position is an endgame
    """
    pieces = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
    pieceCount = 0
    for piece in pieces:
        for color in [chess.WHITE, chess.BLACK]:
            pieceCount += len(list(position.pieces(piece, color)))
    return pieceCount <= 6


if __name__ == '__main__':
    carlsenGames = '../resources/carlsenGames.pgn'
    getEqualEndgameScore(carlsenGames)
