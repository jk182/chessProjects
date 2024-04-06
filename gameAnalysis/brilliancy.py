import re
import chess
from functions import *


def getPolicyHead(leela: engine, positions: list) -> list:
    """
    This function takes a configured LC0 engine and a list of positions and returns Leela's policy header 
    for each position.
    leela: engine
        A configured LC0 engine
    positions: list
        A list of FEN strings containing the positions
    return -> list
        A list containing the policy heads for each position
    """
    policies = list()
    for pos in positions:
        polDict = dict()
        board = chess.Board(pos)
        info = leela.analysis(board, chess.engine.Limit(nodes=1))
        for i in info:
            for j in i.values():
                p = re.findall('P: *\d*\.\d\d%', str(j))
                if (move := str(j).split()[0]) != 'node' and p:
                    polDict[move] = float(p[0].split()[-1][:-1])
        policies.append(polDict)

    return policies


if __name__ == '__main__':
    weights = '/home/julian/Desktop/largeNet'
    leela = configureEngine('lc0', {'WeightsFile': weights, 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})
    positions = ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1']
    print(getPolicyHead(leela, positions))
    leela.quit()
