import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions

import chess
import pandas as pd


def reduceDataset(puzzles: str, minPlays: int):
    """
    This function takes a CSV puzzle dataset and reduces it to only include puzzles played at least minPlay times
    The new dataset will be saved with the same name, just minPlay added at the end
    puzzles: str
        The path to the CSV file
    minPlays: int
        The minimum number of games in order to be included in the new dataset
    """
    df = pd.read_csv(puzzles)
    ndf = df[df['NbPlays'] >= minPlays]
    ndf.reset_index()
    ndf.to_csv(f'{puzzles[:-4]}-{minPlays}.csv')


def solvePuzzle(engine: chess.engine, FEN: str, solution: str, nodes: int = 1, setup: bool = True) -> int:
    """
    This function takes a puzzle position and evaluates if the engine got the right solution.
    It differentiates between getting the first move right and the whole solution.
    engine: chess.engine
        A configured chess engine to solve the puzzles
    FEN: str
        The puzzle position
    solution: str
        The solution moves
    nodes: int
        The nodes the engine useses. The default is 1 since more nodes should be boring
    setup: bool
        If Ture, the first move in the solution will be played since it is the setup for the tactic
    return -> int:
        0: solution is incorrect
        1: first move is correct, but not the whole line
        2: the whole line is correct
    """

    ret = 0
    board = chess.Board(FEN)
    moves = solution.split(' ')
    if setup:
        board.push_uci(moves[0])
        moves = moves[1:]
    for move in moves:
        info = engine.analyse(board, chess.engine.Limit(nodes=nodes))
        engMove = str(info['pv'][0])
        if engMove == move:
            ret = 1
        else:
            return ret
        board.push_uci(move)
    return 2


def calcPerformanceRating(engine: chess.engine, df) -> tuple:
    """
    This function calculates the performance rating for an engine on a give datafram puzzle set
    engine: chess.engine
        A configured chess engine
    df
        Datafram containing the puzzles
    return -> tuple
        A tuple containing the performance rating for partial solutions and full solutions
    """
    partialSol = list()
    fullSol = list()
    for i in df.index:
        score = solvePuzzle(engine, df['FEN'][i], df['Moves'][i])
        rating = df['Rating'][i]
        if score == 0:
            partialSol.append(rating-400)
            fullSol.append(rating-400)
        elif score == 1:
            partialSol.append(rating+400)
            fullSol.append(rating-400)
        else:
            partialSol.append(rating+400)
            fullSol.append(rating+400)

    return (sum(partialSol)/len(partialSol), sum(fullSol)/len(fullSol))


if __name__=='__main__':
    puzzleDB = '~/chess/resources/lichess_db_puzzle.csv'
    plays = 25000
    # reduceDataset(puzzleDB, plays)
    newPDB = f'{puzzleDB[:-4]}-{plays}.csv'
    df = pd.read_csv(newPDB)
    # df = df.sort_values('Popularity', ascending=False)
    pd.set_option('display.max_columns', None)
    print(df)

    maia1100 = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1100.pb', 'UCI_ShowWDL': 'true'})
    maia1900 = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1900.pb', 'UCI_ShowWDL': 'true'})
    print(calcPerformanceRating(maia1100, df))
    print(calcPerformanceRating(maia1900, df))
    maia1100.quit()
    maia1900.quit()
