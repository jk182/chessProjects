import json
import requests
import pandas as pd
import chess
from chess import engine
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def getExplorerInfo(FEN: str, speeds: list = ['blitz', 'rapid', 'classical'], ratings: list = [2000]) -> dict:
    """
    This function gets the explorer information from Lichess as a dictionary
    """
    speedsStr = str(speeds)[1:-1].replace(' ', '').replace("'", "")
    ratingsStr = str(ratings)[1:-1].replace(' ', '')
    print(speedsStr)
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


def compareEngines(engines: list, fens: list) -> list:
    """
    This function calculates the score of various engines for various poisitions
    """
    scores = [ list() for i in range(len(engines)+1) ]
    for fen in fens:
        expInfo = getExplorerInfo(fen)
        scores[-1].append(calcScoreWDL(getExplorerWDL(expInfo)))
        for i, engine in enumerate(engines):
            scores[i].append(calcScoreWDL(getEngineWDL(engine, fen)))
    return scores


if __name__ == '__main__':
    d = getExplorerInfo('rnbqk2r/ppp1bppp/4pn2/3p4/2PP4/6P1/PPQBPPBP/RN2K1NR b KQkq - 5 6')
    printWDL(d)
    leela = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true', 'WDLCalibrationElo': '2000', 'Contempt': '0', 'ContemptMode': 'white_side_analysis', 'WDLEvalObjectivity': '1.0', 'ScoreType': 'WDL_mu'})
    maia = functions.configureEngine('lc0', {'WeightsFile': '/home/julian/chess/maiaNets/maia-1900.pb', 'UCI_ShowWDL': 'true'})
    positions = ['r1bq1rk1/2ppbppp/p1n2n2/1p2p3/3PP3/1B3N2/PPP2PPP/RNBQR1K1 b - - 0 8',
            'rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2',
            'rnb1kb1r/1p3ppp/p2ppn2/6B1/3NPP2/q1N5/P1PQ2PP/1R2KB1R w Kkq - 2 10']
    print(compareEngines([leela, maia], positions))
    leela.quit()
    maia.quit()
