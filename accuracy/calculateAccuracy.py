import chess
from chess import engine, pgn
import numpy as np


def configureEngine(engineName: str, uci_options: dict) -> engine:
    """
    This method configures a chess engine with the given UCI options and returns the 
    engine.
    engineName: str
        The name of the engine (or the command to start the engine)
    uci_optins: dict
        A dictionary containing the UCI options used for the engine
    return -> engine
        A configuered chess.engine
    """
    eng = engine.SimpleEngine.popen_uci(engineName)
    for k, v in uci_options.items():
        eng.configure({k:v})

    return eng


def accuracy(winPercentBefore: float, winPercentAfter: float) -> float:
    """
    This function returns the accuracy score for a given move. The formula for the 
    calculation is taken from Lichess
    winPercentBefore: float
        The win percentage before the move was played (0-100)
    winPercentAfter: float
        The win percentage after the move was payed (0-100)
    return -> float:
        The accuracy of the move (0-100)
    """
    return 103.1668 * np.exp(-0.04354 * (winPercentBefore - winPercentAfter)) - 3.1669


def winP(centipawns: int) -> float:
    """
    This function returns the win percentage for a given centipawn evaluation of a position.
    The formula is taken from Lichess
    centipawns: int
        The evaluation of the position in centipawns
    return -> float:
        The probability of winning given the centipawn evaluation
    """
    return 50 + 50*(2/(1+np.exp(-0.00368208 * centipawns)) - 1)


def gameAccuracy(gamesFile: str, engine: engine, depth: int) -> list:
    """
    This function goes through the games in a PGN file and returns the accuracies of the games.
    gamesFile: str
        The path to the PGN file
    engine: engine
        A configured chess engine
    depth: int
        The depth used on every move
    return -> list
        A list of all the accuracies of the games
    """
    gameAccuracies = list()
    gameNR = 1
    with open(gamesFile, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            print(f'Starting with game {gameNR}...')
            gameNR += 1

            acc = (list(), list())

            board = game.board()
            for move in game.mainline_moves():
                c = board.turn
                cp1 = engine.analyse(board, chess.engine.Limit(depth=depth))["score"].pov(c).score()
                board.push(move)
                if not board.is_game_over():
                    cp2 = engine.analyse(board, chess.engine.Limit(depth=depth))["score"].pov(c).score()
                    if c:
                        acc[0].append(accuracy(winP(cp1), winP(cp2)))
                    else:
                        acc[1].append(accuracy(winP(cp1), winP(cp2)))
            print(sum(acc[0])/len(acc[0]))
            gameAccuracies.append((sum(acc[0])/len(acc[0]), sum(acc[1])/len(acc[1])))

    engine.quit()
    return gameAccuracies


if __name__ == '__main__':
    sf = configureEngine('stockfish', {'Threads': '8', 'Hash': '8192'})
    wijk = '../resources/wijkMasters2024.pgn'
    gameAccuracy(wijk, sf, 15)

