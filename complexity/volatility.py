import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


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
                    gameVol.append((XS-lastXS)**2)
                    lastXS = XS

            vol.append((sum(gameVol)/len(gameVol), len(gameVol)))
    return vol


if __name__ == '__main__':
    capa = '../out/games/capablancaFiltered2.pgn'
    alekhine = '../out/games/alekhine27-40.pgn'
    volCapa = gameVolatility(capa)
    volAlekhine = gameVolatility(alekhine)
    print(len(volCapa), len(volAlekhine))
    print(sum([v[0]*v[1] for v in volCapa])/sum([v[1] for v in volCapa]), sum([v[0]*v[1] for v in volAlekhine])/sum([v[1] for v in volAlekhine]))
