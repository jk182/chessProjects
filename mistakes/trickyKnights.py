import chess
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def refutationInvolvesKnight(sf: chess.engine, board: chess.Board, analysisTime: float = 3, nPVs: int = 3) -> bool:
    """
    This function gets a position after a mistake has happened and checks if the exploitation of this mistake involves a knight move
    """
    mate_score = 100000
    xScoreCutoff = 10
    moveCutoff = 3

    info = sf.analyse(board, chess.engine.Limit(time=analysisTime), multipv=nPVs)
    bestxScore = functions.expectedScore(info[0]['score'].pov(board.turn).score(mate_score=mate_score))
    
    goodPVs = [i['pv'] for i in info if (bestxScore - functions.expectedScore(i['score'].pov(board.turn).score(mate_score=mate_score))) < xScoreCutoff]
    print(goodPVs)

    for pv in goodPVs:
        newBoard = board.copy()
        for i, move in enumerate(pv):
            if moveCutoff * 2 <= i:
                break
            if i % 2 == 1:
                # TODO: should I also check alternatives for the other side?
                continue
            if board.piece_type_at(move.from_square) == chess.KNIGHT:
                nInfo = sf.analyse(newBoard, chess.engine.Limit(time=analysisTime), multipv=nPVs)

                print('KNIGHT', move)
            newBoard.push(move)

    

if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': 4, 'Hash': '8192'})
    fens = ['r1bqr1k1/pp1n2b1/2p5/3pNnPp/3P1P2/1BN5/PPPQ2P1/4RRK1 w - - 1 20', 
            'r3k2r/1bqpbppp/p7/2p5/2B1P1n1/2N2Q2/PPPB1PPP/R3R1K1 b kq - 9 14', 
            '3r2k1/p4pp1/1p5p/2p1N3/4n3/PQP1P2P/1P2qPP1/5RK1 b - - 7 29', 
            'r4rk1/pp3p1p/6p1/2p5/2PnPqb1/2NB4/PP4QP/1K1R3R w - - 4 19', 
            '4r1k1/p4qb1/5n1B/2Rn4/8/6Q1/PP3PPP/5NK1 b - - 0 25']

    for fen in fens:
        board = chess.Board(fen)
        print(refutationInvolvesKnight(sf, board, analysisTime=1))
    sf.quit()
