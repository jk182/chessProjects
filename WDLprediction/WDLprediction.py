import json
import requests
import pandas as pd


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


if __name__ == '__main__':
    d = getExplorerInfo('rnbqk2r/ppp1bppp/4pn2/3p4/2PP4/6P1/PPQBPPBP/RN2K1NR b KQkq - 5 6')
    printWDL(d)
