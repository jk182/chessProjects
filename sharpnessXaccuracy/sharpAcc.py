from chess import engine, pgn
import chess
import numpy as np
import matplotlib.pyplot as plt
import functions


def annotate(gamesFile: str, outfile: str, lc0: engine, sf: engine, nodes: int) -> list:
    """
    This function plays thorugh the games in a file, analyses them and returns a
    list of the evaluations and WDL after every move
    gamesFile: str
        The name of a PGN file containing the games to analyse
    outfile: str
        The path of the output PGN file with the WDL comments
    lc0: engine
        LC0 as an engine
    sf: engine
        Stockfish
    nodes: int
        The number of nodes searched for every move
    return -> list
        A list of lists for each game, containing the WDL and score after every move
    """

    depth = 18
    s = ''
    gameNR = 1
    with open(gamesFile, 'r') as pgn:
        while (game := chess.pgn.read_game(pgn)):
            print(f'Starting with game {gameNR}...')
            gameNR += 1

            if s:
                s += '\n'

            board = game.board()

            # I found no way to add comments to an existing PGN, so I create a new PGN with the comments
            newGame = chess.pgn.Game()
            newGame.headers = game.headers

            for move in game.mainline_moves():
                # print(move)
                # Checks if we have the starting position and need to make a new node
                if board == game.board():
                    node = newGame.add_variation(move)
                else:
                    node = node.add_variation(move)

                board.push(move)
                # The analyse() method gives an error if the game is over (i.e. checkmate, stalemate or insuffucient material)
                if not board.is_game_over():
                    c = not board.turn
                    cp = sf.analyse(board, chess.engine.Limit(depth=depth))["score"].pov(c).score()
                    info = lc0.analyse(board, chess.engine.Limit(nodes=nodes))
                    # score = str(info['score'].white())  # The accuracy metric only needs the win percentage
                    wdl = functions.formatWDL(info['wdl'])
                    s += str(wdl)

                # Adds a comment after every move with the wdl
                node.comment = f'{str(wdl)};{cp}'
            print(newGame, file=open(outfile, 'a+'), end='\n\n')

    # print(s, file=open(outfile, 'w'))


if __name__ == '__main__':
    leela = functions.configureEngine('/home/julian/lc0/build/release/lc0', {'WeightsFile': '/home/julian/Desktop/largeNet', 'UCI_ShowWDL': 'true'})
    stockfish = functions.configureEngine('stockfish', {'Threads': '9', 'Hash': '8192'})
    annotate('../resources/candidates_5000n.pgn', '../resources/candidates_out.pgn', leela, stockfish, 5000)
    leela.quit()
    stockfish.quit()
