import json
import statistics
import pickle
import requests
import pandas as pd
import chess
from chess import engine
import matplotlib.pyplot as plt
import os, sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def getExplorerInfo(FEN: str, speeds: list = ['blitz', 'rapid', 'classical'], ratings: list = [1800, 2000]) -> dict:
    """
    This function gets the explorer information from Lichess as a dictionary
    """
    speedsStr = str(speeds)[1:-1].replace(' ', '').replace("'", "")
    ratingsStr = str(ratings)[1:-1].replace(' ', '')
    rq = requests.get(f'https://explorer.lichess.ovh/lichess?variant=standard&speeds={speedsStr}&ratings={ratingsStr}&fen={FEN}')
    while rq.status_code == 429:
        time.sleep(10)
        print('Too many requests!')
        rq = requests.get(f'https://explorer.lichess.ovh/lichess?variant=standard&speeds={speedsStr}&ratings={ratingsStr}&fen={FEN}')
    res = json.loads(rq.text)
    return res


def printWDL(exp: dict):
    """
    This function prints the overall WDL stats and the stats for each move
    """
    print(f'White: {exp["white"]}, Black: {exp["black"]}, Draws: {exp["draws"]}')
    for move in exp['moves']:
        print(f'Move: {move["san"]}; White: {move["white"]}, Black: {move["black"]}, Draws: {move["draws"]}')
        print(calcScore(int(move["white"]), int(move["black"]), int(move["draws"])))


def calcScore(white: int, black: int, draws: int, isWhite: bool = True) -> float:
    """
    This function calculates the score of a move
    """
    games = white+black+draws
    if games != 1000:
        print(games)
    if games == 0:
        return -1
    if isWhite:
        return (white+0.5*draws)/games
    return (black+0.5*draws)/games


def calcScoreWDL(wdl: list) -> float:
    return calcScore(wdl[0], wdl[2], wdl[1])


def getExplorerWDL(exp: dict) -> list:
    """
    Returns the WDL of an explorer output (note that this is not normalised)
    """
    return [exp['white'], exp['draws'], exp['black']]


def getEngineWDL(engine: chess.engine, FEN: str, nodes: int = 10000) -> list:
    """
    This function calculates the WDL of a given engine for a position
    """
    info = engine.analyse(chess.Board(FEN), chess.engine.Limit(nodes=nodes))
    wdl = list(chess.engine.PovWdl.white(info['wdl']))
    return wdl


def compareEngines(engines: list, fens: list, ratings: list) -> list:
    """
    This function calculates the score of various engines for various poisitions
    """
    minGames = 500
    scores = [ list() for i in range(len(engines)+1) ]
    for fen in fens:
        expInfo = getExplorerInfo(fen, ratings=ratings)
        if expInfo['white']+expInfo['black']+expInfo['draws'] < minGames:
            time.sleep(1)
            continue
        scores[-1].append(calcScoreWDL(getExplorerWDL(expInfo)))
        for i, engine in enumerate(engines):
            scores[i].append(calcScoreWDL(getEngineWDL(engine, fen)))
    return scores


def genPositions(pgnPath: str) -> list:
    """
    This function generates a list of FENs in order to compare the different engines on these positions
    """
    fens = list()
    with open(pgnPath, 'r', encoding="windows-1252") as pgn:
        while game := chess.pgn.read_game(pgn):
            board = game.board()
            for i, move in enumerate(game.mainline_moves()):
                if i == 18:
                    if (fen := board.fen()) not in fens:
                        fens.append(board.fen())
                        break
                board.push(move)
    return fens


def plotScoreDifferences(scores: list, labels: list, filename: str = None):
    """
    This function plotes the differences in scores between engines and the Lichess database
    It is assumed that the last entry in scores is from the Lichess database
    """
    db = scores[-1]
    colors = ['#689bf2', '#f8a978', '#ff87ca', '#beadfa']

    fig, ax = plt.subplots()
    ax.set_facecolor('#e6f7f2')

    for j, s in enumerate(scores[:-1]):
        y = [ abs(s[i]-db[i]) for i in range(len(s)) if db[i] >= 0 ]
        ax.plot(range(len(y)), y, color=colors[j], label=labels[j])

    plt.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.title('Difference between expected and actual scores')
    ax.set_xlim(0, len(y)-1)
    ax.set_ylim(0)
    ax.set_ylabel('Difference to actual score')
    ax.legend()

    if filename:
        plt.savefig(filename, dpi=500)
    else:
        plt.show()


def analyseScores(filenames: list):
    """
    Function to analyse the difference in scores
    """
    for filename in filenames:
        print(filename)
        with open(filename, 'rb') as f:
            scores = pickle.load(f)
        for i in range(len(scores)-1):
            x = [ abs(scores[i][j]-scores[-1][j]) for j in range(len(scores[i])) ]
            print(statistics.median(x))
            print(sum(x)/len(x))


if __name__ == '__main__':
    # fens = genPositions('../resources/2650games2023.pgn')
    # print(fens[:30])
    analyseScores(['../out/WDL1500', '../out/WDL2000', '../out/WDL2500'])
    with open('../out/WDL2500', 'rb') as f:
        scores2500 = pickle.load(f)
    plotScoreDifferences(scores2500, ['LC0 WDL\nContempt 2500'], '../out/expectedScore2500.png')
    
    """
    leela = functions.configureEngine('lc0', {'Threads': '6', 'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLCalibrationElo': '1500', 'Contempt': '0', 'ContemptMode': 'white_side_analysis', 'WDLEvalObjectivity': '1.0', 'ScoreType': 'WDL_mu'})
    maia = functions.configureEngine('lc0', {'Threads': '6', 'WeightsFile': '/home/julian/chess/maiaNets/maia-1500.pb', 'UCI_ShowWDL': 'true'})
    scores = compareEngines([leela, maia], fens, [1400])
    with open('../out/WDL1500', 'wb+') as f:
        pickle.dump(scores, f)
    leela.quit()
    maia.quit()
    leela = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLCalibrationElo': '2000', 'Contempt': '0', 'ContemptMode': 'white_side_analysis', 'WDLEvalObjectivity': '1.0', 'ScoreType': 'WDL_mu'})
    maia = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1900.pb', 'UCI_ShowWDL': 'true'})
    scores = compareEngines([leela, maia], fens, [1800, 2000])
    with open('../out/WDL2000', 'wb+') as f:
        pickle.dump(scores, f)
    leela.quit()
    maia.quit()
    # with open('../out/WDL2000', 'rb') as f:
    #     scores = pickle.load(f)
    leela = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLCalibrationElo': '2500', 'Contempt': '0', 'ContemptMode': 'white_side_analysis', 'WDLEvalObjectivity': '1.0', 'ScoreType': 'WDL_mu'})
    scores = compareEngines([leela], fens, [2500])
    with open('../out/WDL2500', 'wb+') as f:
        pickle.dump(scores, f)
    plotScoreDifferences(scores, ['LC0 WDL\nContempt 2000', 'Maia 1900'])
    leela.quit()
    """
