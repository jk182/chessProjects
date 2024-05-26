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


if __name__ == '__main__':
    fen = '3rnrk1/2qn1pbp/1p4p1/2p1p3/4P3/4B1PP/1PPNQPB1/R4RK1 w - - 0 18'
    print(fen)
    print(movePieceToSquare(fen, 'd2', 'b5'))
