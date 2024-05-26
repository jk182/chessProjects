import Bitboard
import chess

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import functions


def movePieceToSquare(fen: str, oldSquare: str, newSquare: str, changeMove: bool = True) -> str:
    """
    This function moves a piece in a FEN to a new square and returns the new FEN.
    fen: str
        The FEN string of the starting position
    oldSquare, newSquare: str:
        The original square of the piece and the destination square
    changeMove: bool
        If this is True, the new FEN will have the other side to move
    return -> str
        The new FEN string
    """
    board = Bitboard.Bitboard()
    board.setBoardFEN(fen)
    if (newBoard := board.moveToNewSquare(oldSquare, newSquare)):
        newPos = newBoard.toFEN()
        index = fen.index(' ')
        newFEN = f'{newPos}{fen[index:]}'
        if changeMove:
            index = newFEN.index(' ')+1
            if newFEN[index] == 'b':
                newFEN = f'{newFEN[:index]}w{newFEN[index+1:]}'
            else:
                newFEN = f'{newFEN[:index]}b{newFEN[index+1:]}'
        return newFEN
    return None


def findIdealSquare(fen: str, startSquare: str, sf: chess.engine, changeMove: bool = True) -> str:
    """
    This function finds the best square for the piece standing on the startSquare
    fen: str
        The position
    startSquare: str
        The starting square of the piece
    sf: chess.engine
        Stockfish as a configured chess engine in order to evaluate the posioons
    changeMove: bool
        If this is True, the new position will have the other side to move
    return -> str
        The ideal square for the piece
    """
    time = 3
    board = chess.Board(fen)
    startCP = int(str(sf.analyse(board, chess.engine.Limit(time=time))['score'].white()))
    improvement = 0
    white = board.turn
    bestSquare = startSquare

    bitboard = Bitboard.Bitboard()
    bitboard.setBoardFEN(fen)
    evalChanges = dict()
    if bitboard.squareIsEmpty(startSquare):
        return None
    for f in 'abcdefgh':
        for r in range(1, 9):
            newSquare = f'{f}{r}'
            if bitboard.squareIsEmpty(newSquare) and newSquare != startSquare:
                newPos = movePieceToSquare(fen, startSquare, newSquare, changeMove)
                board = chess.Board(newPos)
                newCP = int(str(sf.analyse(board, chess.engine.Limit(time=time))['score'].white()))
                if white:
                    gap = newCP - startCP
                else:
                    gap = startCP - newCP
                evalChanges[newSquare] = gap
    for sq, ev in evalChanges.items():
        if ev > improvement:
            bestSquare = sq
            improvement = ev
    return bestSquare


if __name__ == '__main__':
    sf = functions.configureEngine('stockfish', {'Threads': '10', 'Hash': '8192'})
    fen = '3rnrk1/2qn1pbp/1p4p1/2p1p3/4P3/4B1PP/1PPNQPB1/R4RK1 w - - 0 18'
    # print(fen)
    # print(movePieceToSquare(fen, 'd2', 'b5'))
    # print(findIdealSquare(fen, 'd2', sf, True))
    fen2 = '2bqr1k1/r4pnp/1p3bp1/pPp1p3/2P1P3/3P1NP1/PBQ3BP/4RRK1 w - - 1 20'
    print(findIdealSquare(fen2, 'f3', sf, True))
    sf.quit()
