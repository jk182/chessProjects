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
            # print(i)
            for j in i.values():
                p = re.findall('P: *\d*\.\d\d%', str(j))
                if (move := str(j).split()[0]) != 'node' and p:
                    polDict[move] = float(p[0].split()[-1][:-1])
        policies.append(polDict)

    return policies


def testNets(nets: list, positions: list) -> dict:
    """
    This function tests the policy of different nets for different positions
    nets: list
        The list of different nets
    positions: list
        A list of FEN strings containing the positions
    return -> dict
        A dictionary with the nets as keys and the list of policies as values
    """
    pol = dict()
    for net in nets:
        leela = configureEngine('lc0', {'WeightsFile': net, 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'ture'})
        pol[net] = getPolicyHead(leela, positions)
        leela.quit()
    return pol


if __name__ == '__main__':
    weights = '/home/julian/Desktop/largeNet'
    # leela = configureEngine('lc0', {'WeightsFile': weights, 'UCI_ShowWDL': 'true', 'VerboseMoveStats': 'true'})
    positions = ['rn3rk1/pp3ppp/2pbB3/q7/3P4/2P2N2/P4PPP/R2Q1RK1 w - - 2 16', '4r3/5pk1/ppn1bQ1p/3pPp1P/1q1P1N2/4P3/4N1PK/8 b - - 1 2']
    networks = ['/home/julian/Desktop/smallNet.gz', '/home/julian/Desktop/mediumNet.gz', '/home/julian/Desktop/largeNet', '/home/julian/chess/maiaNets/maia-1900.pb']
    print(testNets(networks, positions))
    # leela.quit()
