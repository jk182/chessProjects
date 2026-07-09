from chess import engine, pgn
import chess
import numpy as np
import subprocess
import re
import math
import statistics


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


def formatWDL(wdl: engine.Wdl) -> list:
    """
    This function takes an engine.wdl and turns it into a list of the WDL from
    white's perspective (0-1000 range)
    wdl: wdl
        The engine.Wdl
    return -> list
        A list containing the W,D,L as integers ranging from 0 to 1000
    """
    wl = []
    wdl_w = engine.PovWdl.white(wdl)
    for w in wdl_w:
        wl.append(w)
    return wl


def sharpnessOG(wdl: list) -> float:
    """
    This function calculates the sharpness based on my own formula
    wdl: lsit
        The WDL
    return -> float
        The sharpness
    """

    w, d, l = wdl

    if min(w, l) < 100:
        return 0

    wd = w - d
    ld = l - d

    return min(w, l)/50 * (1 / (1+np.exp(- (w+l)/1000))) * (333/(d+1))


def sharpnessLC0(wdl: list) -> float:
    """
    This function calculates the sharpness score based on a formula posted by the
    LC0 team on Twitter.
    wdl: list
        The WDL as a list of integers ranging from 0 to 1000
    return -> float
        The shaprness score based on the WDL
    """
    # max() to avoid a division by 0, min() to avoid log(0)
    W = min(max(wdl[0]/1000, 0.0001), 0.9999)
    L = min(max(wdl[2]/1000, 0.0001), 0.9999)

    # max() in order to prevent negative values
    return (max(2/(np.log((1/W)-1) + np.log((1/L)-1)), 0))**2


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
    return min(103.1668100711649 * np.exp(-0.04354415386753951 * (winPercentBefore - winPercentAfter)) - 3.166924740191411 + 1, 100) # the +1 is added in the Lichess formula to account for imperfect analysis


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


def readComment(node, wdl: bool, cp: bool) -> tuple:
    """
    This function takes a game node from a PGN with evaluation comments and returns the evaluation.
    Comment structure: [w, d, l]; cp
    node:
        The game node
    wdl: bool
        If the comment contains a WDL evaluation
    cp: bool
        If the comment contains a centipawn evaluation
    return -> tuple
        A tuple containing the WDL and/or CP evaluations
    """
    if not (wdl or cp):
        return None

    if not node.comment:
        return None

    if wdl and not cp:
        wdlList = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
        return (wdlList)
    if cp and not wdl:
        return (int(float(node.comment)))

    if ';' not in node.comment:
        if '[' in node.comment:
            wdlList = [ int(w) for w in node.comment.replace('[', '').replace(']', '').strip().split(',') ]
            return (wdlList, None)

        return (None, int(float(node.comment)))

    sp = node.comment.split(';')
    wdlList = [ int(w) for w in sp[0].replace('[', '').replace(']', '').strip().split(',') ]
    return (wdlList, int(float(sp[1])))


def modifyFEN(fen: str) -> str:
    """
    This function takes a standard FEN string and removes the halfmove clock and the fullmove number
    """
    fenS = fen.split(' ')
    if not fenS[-2].isnumeric():
        return fen
    modFen = fenS[0]
    for s in fenS[1:-2]:
        modFen = f'{modFen} {s}'
    return modFen


def getNumberOfGames(fen: str) -> int:
    """
    This function returns the number of games in the database with the given position.
    """
    script = '~/coding/chessProjects/novelties/searchPosition.tcl'
    db = '/home/julian/chess/database/gameDB/novelties'
    output = str(subprocess.run(['tkscid', script, db, fen], stdout=subprocess.PIPE).stdout)
    print(output)
    games = re.findall(r'\d+', output)[0]
    return int(games)


def expectedScore(cp: int, k: float = 0.007851) -> float:
    """
    This function calculates the expected score based on the Stockfish evaluation. 
    See gameStatistics/gameStats.py
    """
    # k = 0.007851
    return 50 + 100/math.pi * math.atan(k*cp)


def gameAccuracy(AXSL: float) -> float:
    """
    This function calculates the accuracy of a game given the average expected score loss (AXSL)
    See gameStatistics/gameStats.py
    """
    sigma = 1.55
    offset = 0.25
    if AXSL <= offset:
        return 100
    return 100 * np.exp(-(AXSL-offset)**2/(2*sigma**2))


def lichessGameAccuracy(moveEvaluations: list, expectedScoreFunction = winP, moveAccuracyFunction = accuracy) -> tuple:
    """
    This calculates the game accuracy as used by Lichess (as of May 2026)
    """
    minWinSize = 2
    maxWinSize = 8
    nWindows = 10
    minStDev = 0.5
    maxStDev = 12

    expectedScores = [expectedScoreFunction(cp) for cp in moveEvaluations]

    # Compute the size of the sliding windows used for the volatility
    windowSize = int(len(moveEvaluations) / nWindows)
    windowSize = max(minWinSize, min(windowSize, maxWinSize))

    # Get the win percentages for the windows
    prefixCount = windowSize - 2
    windows = [expectedScores[:windowSize] for _ in range(prefixCount)]
    windows.extend([expectedScores[i:i+windowSize] for i in range(len(expectedScores) - windowSize + 1)])
    
    stDevs = [max(minStDev, min(statistics.pstdev(window), maxStDev)) for window in windows] # Lichess uses the population standard deviation

    accuraciesWhite = list()
    accuraciesBlack = list()

    for i in range(len(expectedScores)-1):
        xsBefore = expectedScores[i]
        xsAfter = expectedScores[i+1]
        weight = stDevs[i]

        if i % 2 == 0:
            accuracy = moveAccuracyFunction(xsBefore, xsAfter)
            accuraciesWhite.append((accuracy, weight))
        else:
            accuracy = moveAccuracyFunction(-xsBefore, -xsAfter)
            accuraciesBlack.append((accuracy, weight))

    weightedMeanWhite = sum([accuracy * weight for accuracy, weight in accuraciesWhite]) / sum([weight for _, weight in accuraciesWhite])
    weightedMeanBlack = sum([accuracy * weight for accuracy, weight in accuraciesBlack]) / sum([weight for _, weight in accuraciesBlack])

    harmonicMeanWhite = len(accuraciesWhite) / sum([1/accuracy for accuracy, _ in accuraciesWhite])
    harmonicMeanBlack = len(accuraciesBlack) / sum([1/accuracy for accuracy, _ in accuraciesBlack])

    return (float((weightedMeanWhite + harmonicMeanWhite)/2), float((weightedMeanBlack+harmonicMeanBlack)/2))


def getEvalsFromPGN(pgnPath: str, lichessAnalysis: bool = False, startEval: int = 20) -> list:
    """
    This function extracts the evaluations from a PGN file
    """
    evaluations = []
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            gameEvals = [startEval]

            node = game
            while not node.is_end():
                node = node.variations[0]
                if lichessAnalysis:
                    if node.eval():
                        gameEvals.append(node.eval().white().score(mate_score=1000))
                    else:
                        print("Evaluation not found")
                        gameEvals.append(gameEvals[-1])
                else:
                    if c := readComment(node, True, True):
                        gameEvals.append(c[1])

            evaluations.append(gameEvals)

    if len(evaluations) == 1:
        return evaluations[0]

    return evaluations


def getGamePhase(board: chess.Board) -> str:
    """
    Heuristic game phase classification from Lichess

    Returns:
        "opening", "middlegame", or "endgame"
    """

    # Count queens, rooks, bishops and knights
    majors_and_minors = sum(
        len(board.pieces(piece, color))
        for piece in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
        for color in (chess.WHITE, chess.BLACK)
    )

    # Endgame heuristic
    if majors_and_minors <= 6:
        return "endgame"

    # Back-rank sparsity
    white_backrank = sum(
        piece is not None and piece.color == chess.WHITE
        for sq in chess.SquareSet(chess.BB_RANK_1)
        if (piece := board.piece_at(sq)) is not None
    )

    black_backrank = sum(
        piece is not None and piece.color == chess.BLACK
        for sq in chess.SquareSet(chess.BB_RANK_8)
        if (piece := board.piece_at(sq)) is not None
    )

    backrank_sparse = white_backrank < 4 or black_backrank < 4

    # Mixedness
    def score(y, white, black):
        if (white, black) == (0, 0):
            return 0
        if (white, black) == (1, 0):
            return 1 + (8 - y)
        if (white, black) == (2, 0):
            return 2 + (y - 2) if y > 2 else 0
        if (white, black) == (3, 0):
            return 3 + (y - 1) if y > 1 else 0
        if (white, black) == (4, 0):
            return 3 + (y - 1) if y > 1 else 0
        if (white, black) == (0, 1):
            return 1 + y
        if (white, black) == (1, 1):
            return 5 + abs(4 - y)
        if (white, black) == (2, 1):
            return 4 + (y - 1)
        if (white, black) == (3, 1):
            return 5 + (y - 1)
        if (white, black) == (0, 2):
            return 2 + (6 - y) if y < 6 else 0
        if (white, black) == (1, 2):
            return 4 + (7 - y)
        if (white, black) == (2, 2):
            return 7
        if (white, black) == (0, 3):
            return 3 + (7 - y) if y < 7 else 0
        if (white, black) == (1, 3):
            return 5 + (7 - y)
        if (white, black) == (0, 4):
            return 3 + (7 - y) if y < 7 else 0
        return 0

    mixedness = 0
    for rank in range(7):
        for file in range(7):
            white = black = 0
            for dr in (0, 1):
                for df in (0, 1):
                    piece = board.piece_at(chess.square(file + df, rank + dr))
                    if piece:
                        if piece.color == chess.WHITE:
                            white += 1
                        else:
                            black += 1
            mixedness += score(rank + 1, white, black)

    # Middlegame heuristics
    if (majors_and_minors <= 10 or backrank_sparse or mixedness > 150):
        return "middlegame"

    return "opening"
