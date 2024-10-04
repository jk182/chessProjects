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
    analysisTime = 2
    board = chess.Board(fen)
    pv = engine.analyse(board, chess.engine.Limit(time=analysisTime))['pv']
    print(analysePV(board, pv))


def analysePV(board: chess.Board, pv: list) -> str:
    """
    This function looks for piece manoeuvres in a PV
    return -> str
        The final move in the manoeuvre
    """
    firstMove = pv[0]
    print(pv)
    if (piece := board.piece_type_at(firstMove.from_square)) == chess.PAWN:
        return None
    for i, move in enumerate(pv):
        if i % 2 == 0:
            if not piece == board.piece_type_at(move.from_square):
                print("other piece")
                break
            endSquare = move.to_square
        board.push(move)
    return chess.SQUARE_NAMES[endSquare]


if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': '4', 'Hash': '8192'})
    fen = 'r1bq1rk1/2pnbppp/p2p1n2/1p2p3/4P3/1BPP1N1P/PP3PP1/RNBQR1K1 w - - 1 11'
    print(findPieceManoeuvre(fen, sf))
    sf.quit()
