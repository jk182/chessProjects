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


def plotExpectedScore(pgnPath: str):
    """
    This plots the expected score over the course of each game in the PGN in one line plot
    """
    data = list()
    labels = list()
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

    plotting_helper.plotLineChart(data, 'Moves', 'Expected Score (white POV)', 'Expected score', labels, hlineHeight=50)


if __name__ == '__main__':
    """"
    capa = '../out/games/capablancaFiltered2.pgn'
    alekhine = '../out/games/alekhine27-40.pgn'
    volCapa = gameVolatility(capa)
    volAlekhine = gameVolatility(alekhine)
    print(len(volCapa), len(volAlekhine))
    print(sum([v[0]*v[1] for v in volCapa])/sum([v[1] for v in volCapa]), sum([v[0]*v[1] for v in volAlekhine])/sum([v[1] for v in volAlekhine]))
    """

    vol = gameVolatility('../out/games/wildGames-out.pgn')
    print(vol)
    print(gameVolatility('../out/games/tameWins-out.pgn'))
    # plotExpectedScore('../out/games/wildGames-out.pgn')
