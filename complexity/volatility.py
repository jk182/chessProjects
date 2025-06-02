import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
import matplotlib.pyplot as plt
import plotting_helper


def gameVolatility(pgnPath: str) -> list:
    """
    This calculates the volatility of each game in the given PGN file
    return -> list
        List containing the volatility value for each game
    """
    vol = list()
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            gameVol = list()
            lastXS = functions.expectedScore(20)
            node = game
            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = functions.readComment(node, True, True)[1]
                    XS = functions.expectedScore(cp)
                    gameVol.append(abs(XS-lastXS)**2)
                    lastXS = XS
            if node.comment:
                cp = functions.readComment(node, True, True)[1]
                XS = functions.expectedScore(cp)
                gameVol.append(abs(XS-lastXS)**2)
                lastXS = XS

            vol.append(((sum(gameVol)/len(gameVol))**0.5, len(gameVol)))
    return vol


def playerVolatility(pgnPath: str) -> dict:
    playerVol = dict()
    a = 2
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            white = game.headers["White"]
            black = game.headers["Black"]

            gameVol = list()
            lastXS = functions.expectedScore(20)
            node = game
            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = functions.readComment(node, True, True)[1]
                    xs = functions.expectedScore(cp)
                    gameVol.append(abs(xs-lastXS)**a)
                    lastXS = xs
            if node.comment:
                cp = functions.readComment(node, True, True)[1]
                xs = functions.expectedScore(cp)
                gameVol.append(abs(xs-lastXS)**a)

            for player in [white, black]:
                if player not in playerVol.keys():
                    playerVol[player] = list()
                playerVol[player].append(((sum(gameVol)/len(gameVol))**(1/a), len(gameVol)))
        return playerVol


def plotExpectedScore(pgnPath: str, filename: str = None):
    """
    This plots the expected score over the course of each game in the PGN in one line plot
    """
    data = list()
    labels = ['Carlsen-Erigaisi, 2025', 'Carlsen-Rapport, 2022', 'Tal-Koblents, 1957']
    with open(pgnPath, 'r') as pgn:
        while game := chess.pgn.read_game(pgn):
            gxs = list()
            whitePlayer = game.headers['White'].split(',')[0]
            blackPlayer = game.headers['Black'].split(',')[0]
            year = game.headers['Date'][:4]
            labels.append(f'{whitePlayer}-{blackPlayer}, {year}')

            node = game
            while not node.is_end():
                node = node.variations[0]
                if node.comment:
                    cp = functions.readComment(node, True, True)[1]
                    gxs.append(functions.expectedScore(cp))
            if node.comment:
                cp = functions.readComment(node, True, True)[1]
                gxs.append(functions.expectedScore(cp))
            data.append(gxs)

    plotting_helper.plotLineChart(data, 'Move number', "White's expected score", 'Expected score after each move', labels, hlineHeight=50, filename=filename)


if __name__ == '__main__':
    """"
    capa = '../out/games/capablancaFiltered2.pgn'
    alekhine = '../out/games/alekhine27-40.pgn'
    volCapa = gameVolatility(capa)
    volAlekhine = gameVolatility(alekhine)
    print(len(volCapa), len(volAlekhine))
    print(sum([v[0]*v[1] for v in volCapa])/sum([v[1] for v in volCapa]), sum([v[0]*v[1] for v in volAlekhine])/sum([v[1] for v in volAlekhine]))
    """

    vol = gameVolatility('../out/games/volatility.pgn')
    print(vol)
    plotExpectedScore('../out/games/volatility.pgn', '../out/volatility/expectedScore.png')
    playerVol = playerVolatility('../out/games/wijkMasters2025-out.pgn')
    for k, v in playerVol.items():
        volatility = [a[0] for a in v]
        print(f'{k}: {sum(volatility)/len(volatility)}')

    games = ['Carlsen-Erigaisi, 2025', 'Carlsen-Rapport, 2022', 'Tal-Koblents, 1957']
    plotting_helper.plotPlayerBarChart([[v[0]] for v in vol], games, 'Volatility', 'Volatility for different games', ['Volatility'], filename='../out/volatility/volatility.png')
