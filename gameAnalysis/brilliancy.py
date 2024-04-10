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
        policies.append((pos, polDict))

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
    """
        Sicilian Najdorf
        Sicilian Kan
        Ruy Lopez: 8.c3
        Ruy Lopez: 7...d6 8.c3 O-O 9.h3
        Semi-Slav: 4...e6
        Semi-Slav: Moscow or Anit-Moscow
        QGD: Tartakower 7...b6
        Catalan: Open 7...a6
        French: 5...Qb6
        Symmetrical English
        Ruy Lopez Middlegame
        Winawer Poisoned Pawn
        Caruana-MVL before bishop sac
    """
    openings = ['rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6', 
                'rnbqkbnr/1p1p1ppp/p3p3/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 5',
                'r1bq1rk1/2ppbppp/p1n2n2/1p2p3/4P3/1BP2N2/PP1P1PPP/RNBQR1K1 b - - 0 8',
                'r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - - 0 9',
                'rnbqkb1r/pp3ppp/2p1pn2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5',
                'rnbqkb1r/pp3pp1/2p1pn1p/3p2B1/2PP4/2N2N2/PP2PPPP/R2QKB1R w KQkq - 0 6',
                'rnbq1rk1/p1p1bpp1/1p2pn1p/3p4/2PP3B/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8',
                'rnbq1rk1/1pp1bppp/p3pn2/8/2pP4/5NP1/PPQ1PPBP/RNB2RK1 w - - 0 8',
                'r1b1kbnr/pp3ppp/1qn1p3/2ppP3/3P4/2P2N2/PP3PPP/RNBQKB1R w KQkq - 3 6',
                'r1bqk1nr/pp1pppbp/2n3p1/2p5/2P5/2N3P1/PP1PPPBP/R1BQK1NR w KQkq - 4 5',
                'r2qr1k1/1b2bp2/p2p1np1/1pnPp1Bp/P1p1P3/2P2NNP/1PBQ1PP1/R3R1K1 w - - 2 21',
                'rnbqk2r/pp2nppp/4p3/2ppP3/3P2Q1/P1P5/2P2PPP/R1B1KBNR b KQkq - 2 7',
                'rnb1k2r/1p1n1pp1/p3p2p/2bq4/3NN3/2P1Q1B1/6PP/3RKB1R w Kkq - 3 18']
    networks = ['/home/julian/Desktop/smallNet.gz', '/home/julian/Desktop/mediumNet.gz', '/home/julian/Desktop/largeNet', '/home/julian/chess/maiaNets/maia-1900.pb']
    print(testNets(networks, openings))
    # leela.quit()
