import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions
from chess import engine, pgn, Board
import chess


def findPieceManoeuvre(fen: str, engine: chess.engine) -> str:
    """
    This function finds a piece manoeuvre in the top line of an engine
    fen: str
        The position in question
    engine: chess.engine
        Configured chess engine to find the piece manoeuvre
    return -> str
        The final move in the manoeuvre or None if the top line is no piece manoeuvre
    """
    analysisTime = 4
    pvCount = 3
    board = chess.Board(fen)
    multiPV = engine.analyse(board, chess.engine.Limit(time=analysisTime), multipv=pvCount)
    for info in multiPV:
        pv = info['pv']
        print(analysePV(board.copy(), pv))


def analysePV(board: chess.Board, pv: list) -> list:
    """
    This function looks for piece manoeuvres in a PV
    return -> str
        The final move in the manoeuvre
    """
    firstMove = pv[0]
    otherMove = False
    moves = list()
    if (piece := board.piece_type_at(firstMove.from_square)) == chess.PAWN:
        return None
    lastSquare = firstMove.from_square
    for i, move in enumerate(pv):
        if i % 2 == 0:
            if not piece == board.piece_type_at(move.from_square) or not lastSquare == move.from_square:
                if otherMove:
                    break
                otherMove = True
                continue
            moves.append(move.uci())
            lastSquare = move.to_square
            otherMove = False

        board.push(move)
    print(pv)
    return moves


if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': '4', 'Hash': '8192'})
    fen = 'r1bq1rk1/2pnbppp/p2p1n2/1p2p3/4P3/1BPP1N1P/PP3PP1/RNBQR1K1 w - - 1 11'
    fen = '3rnrk1/2qn1pbp/1p4p1/2p1p3/4P3/4B1PP/1PPNQPB1/R4RK1 w - - 0 18'
    fen = '4rrk1/1bpR1p2/1pq1pQp1/p3P2p/P1PR3P/5N2/2P2PP1/6K1 w - h6 0 31'
    print(findPieceManoeuvre(fen, sf))
    sf.quit()
