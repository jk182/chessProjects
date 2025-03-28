import berserk
import matplotlib.pyplot as plt
import time


def getPositionScore(client, position: str, ratings: list) -> float:
    """
    This function calculates the score from White's perspective in a given position for the given ratings
    client
        Lichess API client
    position: str
        FEN string of the position
    retings: list
        The ratings (as strings) to look at
    return -> float:
        The score from White's perspective
    """
    info = client.opening_explorer.get_lichess_games(position=position, ratings=ratings)
    return (info['white']+0.5*info['draws']) / (info['white']+info['draws']+info['black'])


def plotOpeningScores(client, openings: dict, title: str, filename: str = None):
    """
    This plots the scores for all rating ranges in the given openings
    client
        Lichess API client
    openings: dict
        Dictionary with opening names as keys and FENs as values
    title: str
        Title for the plot
    filename: str
        Path to where the plot should be saved
        If no path is given, the plot will be shown instead of saved.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#e6f7f2')
    colors = ['#6096B4', '#7ed3b2', '#FF87CA', '#BEADFA', '#F8A978', '#E97777', '#435560'] 
    ratings = ['400', '1000', '1200', '1400', '1600', '1800', '2000', '2200', '2500']

    for i, (name, position) in enumerate(openings.items()):
        scores = [getPositionScore(client, position, [rating]) for rating in ratings if time.sleep(0.7) is None]
        plt.plot(scores, label=name, color=colors[i%len(openings)])

    ax.set_xlabel('Lichess rating')
    ax.set_ylabel('Score for white')
    ax.set_xticks(range(len(ratings)), ratings)
    ax.set_xlim(0, len(ratings)-1)
    plt.title(title)
    fig.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
    plt.legend()
    if filename:
        plt.savefig(filename, dpi=400)
    else:
        plt.show()


if __name__ == '__main__':
    with open('../resources/tbToken', 'r') as tokenFile:
        token = tokenFile.read().strip()

    session = berserk.TokenSession(token)
    client = berserk.Client(session=session)
    # print(client.opening_explorer.get_lichess_games(position='rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2', ratings=['1000']))
    position = 'rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2'
    startMoves = {'1.e4': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1', 
                  '1.d4': 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1',
                  '1.c4': 'rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1',
                  '1.Nf3': 'rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1',
                  '1.b3': 'rnbqkbnr/pppppppp/8/8/8/1P6/P1PPPPPP/RNBQKBNR b KQkq - 0 1',
                  # '1.f4': 'rnbqkbnr/pppppppp/8/8/5P2/8/PPPPP1PP/RNBQKBNR b KQkq - 0 1',
                  '1.g3': 'rnbqkbnr/pppppppp/8/8/8/6P1/PPPPPP1P/RNBQKBNR b KQkq - 0 1'}
    e4Openings = {'1.e4 e5': 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
                  '1.e4 c5': 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
                  '1.e4 e6': 'rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
                  '1.e4 c6': 'rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
                  '1.e4 g6': 'rnbqkbnr/pppppp1p/6p1/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
                  '1.e4 d5': 'rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2'}
                  # '1.e4 Nf6': 'rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2'}
    d4Openings = {'QGD': 'rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3',
                  'QGA': 'rnbqkbnr/ppp1pppp/8/8/2pP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3',
                  'Slav': 'rnbqkbnr/pp2pppp/2p5/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3',
                  'KID': 'rnbqk2r/ppppppbp/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4',
                  'Grünfeld': 'rnbqkb1r/ppp1pp1p/5np1/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4',
                  'Nimzo-Indian': 'rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4',
                  'Dutch': 'rnbqkbnr/ppppp1pp/8/5p2/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2'}

    openings = {'Najdorf': 'rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6',
                'Kings Gambit': 'rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2',
                'Kings Indian': 'rnbqk2r/ppp1ppbp/3p1np1/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 0 5',
                'Ruy Lopez': 'r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3',
                'Smith-Morra Gambit': 'rnbqkbnr/pp1ppppp/8/2p5/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2',
                'Marshall Attack': 'r1bq1rk1/2p1bppp/p1n2n2/1p1pp3/4P3/1BP2N2/PP1P1PPP/RNBQR1K1 w - - 0 9',
                'Start Pos': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'}
    mainLines = {'Ruy Lopez': 'r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3',
                 'Italian': 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3',
                 'Open Sicilian': 'rnbqkbnr/pp2pppp/3p4/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3',
                 'QGD': 'rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4',
                 'KID': 'rnbqk2r/ppppppbp/5np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4',
                 'Grünfeld': 'rnbqkb1r/ppp1pp1p/5np1/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4',
                 'Nimzo-Indian': 'rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4'}
    gambits = {"King's Gambit": 'rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 0 2',
               'Smith-Morra Gambit': 'rnbqkbnr/pp1ppppp/8/2p5/3PP3/8/PPP2PPP/RNBQKBNR b KQkq - 0 2',
               'Marshall Attack': 'r1bq1rk1/2p1bppp/p1n2n2/1p1pp3/4P3/1BP2N2/PP1P1PPP/RNBQR1K1 w - - 0 9',
               'Budapest Gambit': 'rnbqkb1r/pppp1ppp/5n2/4p3/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3',
               'Englund Gambit': 'rnbqkbnr/pppp1ppp/8/4p3/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2',
               'Benko Gambit': 'rnbqkb1r/p2ppppp/5n2/1ppP4/2P5/8/PP2PPPP/RNBQKBNR w KQkq - 0 4'}
    # plotOpeningScores(client, e4Openings, 'Scores of responses to 1.e4')
    # plotOpeningScores(client, mainLines, 'Scores in different openings')
    # plotOpeningScores(client, d4Openings, 'Scores of d4 openings', filename='../out/lichessOpeningsd4.png')
    plotOpeningScores(client, startMoves, 'Scores of different first moves')
    # plotOpeningScores(client, gambits, 'Scores of different gambits', filename='../out/lichessOpeningsGambits.png')
