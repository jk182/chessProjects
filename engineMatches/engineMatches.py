import chess
from chess import engine, pgn
from datetime import date
import configparser


"""
    This function sets the UCI options for an engine
    engineName: The name of the engine, with which it can be called from the command line
    uci_options: Dictionary with the UCI options of the engine
    return: chess.engine.SimpleEngine with the UCI options set
"""
def configureEngine(engineName, uci_options):
    engine = chess.engine.SimpleEngine.popen_uci(engineName)
    for k, v in uci_options.items():
        engine.configure({k:v})

    return engine


"""
    n: Number of games in each starting positions
    startingPositions: Dictionary with FEN and name of the starting positions
    engineFileWhite: The config file of the engine playing white in the first game
    engineFileBlack: The config file of the engine playing black in the first game
    pgnFile: Path to the file, where the PGNs should be written to
"""
def play(n, startingPositions, engineFileWhite, engineFileBlack, pgnFile):
    # Reading all the information from the config files for both engines
    configFileEngine1 = engineFileWhite
    configFileEngine2 = engineFileBlack

    configEngine1 = configparser.ConfigParser()
    configEngine2 = configparser.ConfigParser()

    configEngine1.read(configFileEngine1)
    configEngine2.read(configFileEngine2)

    engine1Name = configEngine1['general']['name']
    engine2Name = configEngine2['general']['name']

    time1 = float(configEngine1['general']['time'])
    time2 = float(configEngine2['general']['time'])

    uci_options1 = configEngine1._sections['uci_options']
    uci_options2 = configEngine2._sections['uci_options']

    # Setting the UCI options for each engine
    engine1 = configureEngine(engine1Name, uci_options1)
    engine2 = configureEngine(engine2Name, uci_options2)
    
    for position in startingPositions.keys():
        for i in range(n):
            game = chess.pgn.Game()
            d = date.today()
            game.headers['Event'] = startingPositions[position]
            game.headers['Site'] = 'Enigne Match'
            game.headers['Date'] = d.strftime('%d.%m.%Y')
            game.headers['Round'] = i + 1
            game.setup(position)
            board = game.board()
            node = game


            while not board.is_game_over():
                if (board.turn + i) % 2 == 1:
                    # This is the engine playing white for the current game
                    r = engine1.play(board, chess.engine.Limit(time=time1))
                else:
                    r = engine2.play(board, chess.engine.Limit(time=time2))
                print(r.move)
                # info = engine2.analyse(board, chess.engine.Limit(depth=2))
                # print(info['wdl'])
                node = node.add_variation(r.move)
                board.push(r.move)
            
            if i % 2 == 0:
                white = engine1Name
                black = engine2Name
            else:
                white = engine2Name
                black = engine1Name

            game.headers['White'] = white
            game.headers['Black'] = black
            game.headers['Result'] = board.result()
            # print(game)
            print(game, file=open(pgnFile, 'a+'), end='\n\n')
            print(f'Game {i+1} of {n} in the line {startingPositions[position]} is finished')

    engine1.quit()
    engine2.quit()


if __name__ == '__main__':
    startingPos = {'rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N1B2P/PP3PP1/R2QKBNR b KQ - 2 6': 'KID', 'r1b1k2r/1p2pp2/p2p1n1b/2q5/3NP1n1/2N5/PPP1Q1PP/R3KBBR w KQkq - 7 15': 'Najdorf 6.Bg5 pawn sac'}
    startingPos2 = {'rnbq1rk1/p1p1bppp/4pn2/1p2N3/2pP4/6P1/PPQ1PPBP/RNB2RK1 b - - 1 8': 'Carlsens 8.Ne5', 'rnbq1rk1/p1p1bppp/4pn2/1p6/P1pP4/5NP1/1PQ1PPBP/RNB2RK1 b - - 0 8': '8.a4'}

    KID = {'rnbq1rk1/pp2ppbp/3p1np1/2p5/2PPP3/2N1B2P/PP3PP1/R2QKBNR w KQ - 0 7': 'Makogonov 6...c5',
            'r1bq1rk1/ppp1ppbp/n2p1np1/8/2PPP3/2N1B2P/PP3PP1/R2QKBNR w KQ - 2 7': 'Makogonov 6...Na6',
            'r1bq1rk1/pppnppbp/3p1np1/8/2PPP3/2N1B2P/PP3PP1/R2QKBNR w KQ - 2 7': 'Makogonov 6...Nbd7',
            'r1bq1rk1/ppp1ppbp/2np1np1/8/2PPP3/2N1B2P/PP3PP1/R2QKBNR w KQ - 2 7': 'Makogonov 6...Nc6',
            'rnbq1rk1/p1p1ppbp/1p1p1np1/8/2PPP3/2N1B2P/PP3PP1/R2QKBNR w KQ - 0 7': 'Makogonov 6...b6'}
    
    slav = {'rnbqkb1r/p4p2/2p1pn2/1p2P1B1/2pP4/2N5/PP3PPP/R2QKB1R b KQkq - 0 10': 'Botvinnik Variation',
            'rnbqkb1r/pp3p2/2p1pn1p/6p1/2pPP3/2N2NB1/PP3PPP/R2QKB1R b KQkq - 1 8': 'Anti Moscow Gambit',
            'rnb1kb1r/pp3pp1/2p1pq1p/3p4/2PP4/2N2N2/PP2PPPP/R2QKB1R w KQkq - 0 7': 'Moscow Variation',
            'rnbqkb1r/p3pppp/2p2n2/1p6/2pPP3/2N2N2/PP3PPP/R1BQKB1R w KQkq - 0 6': 'Geller Gambit'}
    
    dutch = {'rnbqkbnr/ppppp2p/6p1/5pB1/3P4/8/PPP1PPPP/RN1QKBNR w KQkq - 0 3': '2...g6', 
            'rnbqkbnr/ppppp1p1/7p/5pB1/3P4/8/PPP1PPPP/RN1QKBNR w KQkq - 0 3': '2...h6'}

    alekhine = {'rnbqkb1r/ppp1pp1p/1n1p2p1/4P3/2PP1P2/8/PP4PP/RNBQKBNR w KQkq - 0 6' : 'Alekhine 5...g6'}

    scandi = {'rnbqkb1r/ppp1pp1p/1n4p1/8/2PP4/5N2/PP3PPP/RNBQKB1R w KQkq - 0 6': 'Scandi'}

    gameAnalysis = {'rnb1kb1r/pppp4/4pq1p/5ppQ/3P3B/8/PPP2PPP/RN2KBNR b KQkq - 1 7': '7.Qh5+',
                    'rnb2b1r/pppp1k2/4p2p/8/3P1p2/8/PPP2PPP/RN2KBNR w KQ - 0 11': '10...gxf4',
                    'r6r/pppb1k2/7p/3pb3/5p2/2PB4/PP1N1PPP/2KR3R w - - 2 18': '17...Bd7',
                    '7r/ppp5/3b1k2/4r2p/2BR4/2P3p1/PP3P1P/2K4R w - - 0 28': '27...fxg3',
                    '7r/ppp5/3b4/4k3/2B4p/2P3P1/PP1K3P/5R2 w - - 2 33': '32...Ke5'}

    config1 = 'config/engine1.ini'
    config2 = 'config/engine2.ini'
    pgnFile = 'out/gameAnalysis.pgn'
    
    play(4, gameAnalysis, config1, config2, pgnFile)
