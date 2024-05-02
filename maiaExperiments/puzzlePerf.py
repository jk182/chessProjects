import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions

import chess
import pandas as pd
import matplotlib.pyplot as plt
import pickle


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


def ratingBand(df, minRating: int, maxRating):
    """
    This function filters out all the puzzles in a given dataframe which do not have a rating in the rating band
    df:
        The dataframe containing the puzzles
    minRating: int
        The minimal rating in the band (included)
    maxRating: int
        The maximal rating in the band (excludec)
    return
        Dataframe with only the puzzles int the rating band
    """
    ndf = df.loc[(df['Rating'] >= minRating) & (df['Rating'] < maxRating)]
    return ndf.reset_index()


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

    white = board.turn
    for move in moves:
        info = engine.analyse(board, chess.engine.Limit(nodes=nodes))
        # Check if we are actually trying to find the best move
        if white == board.turn:
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
        Dataframe containing the puzzles
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


def calcPuzzleSolutions(engine: chess.engine, df) -> list:
    """
    This function returns a list of tuples with the puzzle FEN and the engine's score on that puzzle
    engine: chess.engine
        A configured chess engine
    df
        Dataframe containing the puzzles
    retrun -> list
        A list of tuples (FEN, solution)
    """
    solutions = list()
    for i in df.index:
        fen = df['FEN'][i]
        solutions.append((fen, solvePuzzle(engine, fen, df['Moves'][i])))
    return solutions


def filterSolutions(df, solutions: list, fil: dict) -> list:
    """
    This function filters out solutions based on criteria given in the filter fil
    df
        Dataframe containing the puzzles
    solutions: list
        List of positions with the score, as returned by calcPuzzleSolutions
    fil: dict
        Dictionary used to filter the soltions. Keys are the column names in the dataframe and the 
        values are the values in the specified column
    """
    filteredSolutions = list()
    positions = [s[0] for s in solutions]
    for i in df.index:
        fen = df['FEN'][i]
        if fen not in positions:
            continue
        for k,v in fil.items():
            if v not in df[k][i]:
                break
        else:
            sol = solutions[positions.index(fen)]
            filteredSolutions.append(sol)
    return filteredSolutions


def calcPuzzleScore(solutions: list) -> tuple:
    """
    This function calculates the score (0-1) for a given output of the calcPuzzleSolutions method
    solutions: list
        A list containing the FENs ánd scores on the puzzles (see calcPuzzleSolutions)
    return -> tuple
        A tuple containing the score (from 0 to 1) for partial and full solutions
    """
    partialSol = 0
    fullSol = 0
    for s in solutions:
        score = s[1]
        if score == 1:
            partialSol += 1
        if score == 2:
            fullSol += 1
    return ((partialSol+fullSol)/len(solutions), fullSol/len(solutions))


def plotPuzzlePerformance(puzzlePerf: dict, engineNames: list):
    """
    This function plots the performance of different engines on various datasets
    puzzlePerf: dict
        This dictionary has the name of the puzzle dataset as key (e.g. 1500-1800 puzzles) and a list of the 
        scores from the engines as values.
    engineNames: list
        The names of the engines, sorted the same way as in the values of the puzzlePerf dictionary
    """
    fig, ax = plt.subplots()
    ax.set_facecolor('#e6f7f2')

    plt.xticks(ticks=range(1, len(engineNames)+1), labels=engineNames)
    colors = [('#93BFCF', '#6096B4'), ('#b9e6d3', '#7ed3b2'), ('#FFC4E1', '#FF87CA'), ('#FF9F9F', '#E97777'), ('#6E7C7C', '#435560')] 

    width = 2 / (4 * (len(puzzlePerf.keys())+1))
    offset = -width*(len(puzzlePerf.keys())-0.5)

    for puz, perf in puzzlePerf.items():
        colorIndex = list(puzzlePerf.keys()).index(puz) % len(colors)
        ax.bar([ i+1+offset for i in range(len(perf)) ], [ p[0] for p in perf ], color=colors[colorIndex][0], edgecolor='black', linewidth=0.5, width=width) 
        ax.bar([ i+1+offset+width for i in range(len(perf)) ], [ p[1] for p in perf ], color=colors[colorIndex][1], edgecolor='black', linewidth=0.5, width=width, label=f'{puz}') 
        offset += 2*width
    ax.legend()

    plt.show()


if __name__=='__main__':
    puzzleDB = '~/chess/resources/lichess_db_puzzle.csv'
    plays = 20000
    # reduceDataset(puzzleDB, plays)
    newPDB = f'{puzzleDB[:-4]}-{plays}.csv'
    df = pd.read_csv(newPDB)
    # df = df.sort_values('Popularity', ascending=False)
    pd.set_option('display.max_columns', None)
    print(df)


    maia1100 = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1100.pb', 'UCI_ShowWDL': 'true'})
    maia1500 = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1500.pb', 'UCI_ShowWDL': 'true'})
    maia1900 = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1900.pb', 'UCI_ShowWDL': 'true'})

    engineNames = ['Maia 1100', 'Maia 1500', 'Maia 1900']
    engines = [maia1100, maia1500, maia1900]

    puzzlePerf = dict()

    ratings = [0, 1200, 1500, 1800, 2100, 2400, 2700]
    """
    for i in range(len(ratings)-1):
        lower = ratings[i]
        upper = ratings[i+1]
        bandDF = ratingBand(df, lower, upper)
        
        puzzlePerf[f'{lower}-{upper}'] = list()
        for e in engines:
            solutions = calcPuzzleSolutions(e, bandDF)
            with open(f'../out/puzzleSol{engineNames[engines.index(e)]}-{upper}-{plays}.pkl', 'wb+') as f:
                pickle.dump(solutions, f)
            puzzlePerf[f'{lower}-{upper}'].append(calcPuzzleScore(solutions))

    with open(f'../out/maiaData-{plays}.pkl', 'wb+') as f:
        pickle.dump(puzzlePerf, f)

    """
    with open(f'../out/maiaData-{plays}.pkl', 'rb') as f:
        puzzlePerf = pickle.load(f)
    # print(puzzlePerf)
    pfN = dict()
    for k,v in puzzlePerf.items():
        if not k == '2400-2700':
            pfN[k] = v
    # plotPuzzlePerformance(pfN, engineNames)

    pPerfPhase = dict()
    for e in engineNames:
        for phase in ['opening', 'middlegame', 'endgame']:
            filteredSolutions = list()
            for upper in [1200, 1500, 1800, 2100, 2400]:
                with open(f'../out/puzzleSol{e}-{upper}-{plays}.pkl', 'rb') as f:
                    solution = pickle.load(f)
                fil = {'Themes': phase}
                filteredSolutions += filterSolutions(df, solution, fil)
            score = calcPuzzleScore(solution)
            print(e, phase, score)
            if phase not in pPerfPhase.keys():
                pPerfPhase[phase] = [score]
            else:
                pPerfPhase[phase].append(score)
    print(pPerfPhase)
    plotPuzzlePerformance(pPerfPhase, engineNames)
    
    maia1100.quit()
    maia1500.quit()
    maia1900.quit()
