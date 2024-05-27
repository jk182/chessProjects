class Bitboard:
    def __init__(self, empty=False):
        self.board = list()
        # TODO: castleing should also be included

        if empty:
            for i in range(12):
                self.board.append(0x0)
        else:
            self.board.append(0x00FF000000000000)   # Black Pawns
            self.board.append(0x4200000000000000)   # Black Knights
            self.board.append(0x2400000000000000)   # Black Bishops
            self.board.append(0x8100000000000000)   # Black Rooks
            self.board.append(0x1000000000000000)   # Black Queen
            self.board.append(0x0800000000000000)   # Black King
            self.board.append(0x000000000000FF00)   # White Pawns
            self.board.append(0x0000000000000024)   # White Knights
            self.board.append(0x0000000000000042)   # White Bishops
            self.board.append(0x0000000000000081)   # White Rooks
            self.board.append(0x0000000000000010)   # White Queen
            self.board.append(0x0000000000000008)   # White King


    def setBoard(self, board):
        self.board = board


    def getBoard(self):
        b = 0x0
        for piece in self.board:
            b = b | piece
        return b


    def printBoard(self):
        b = bin(self.getBoard())[2:]
        b = f'{"0"*(64-len(b))}{b}'
        for i in range(8):
            print(b[i*8:(i+1)*8])


    def setBoardFEN(self, fen):
        emptyBoard = list()
        for i in range(12):
            emptyBoard.append(0x0)
        self.setBoard(emptyBoard)
        pos = 0
        pieces = 'pnbrqkPNBRQK'
        for s in fen:
            if s == '/':
                continue
            if s in pieces:
                index = pieces.index(s)
                self.board[index] |= 2**(63-pos)
                pos += 1
                continue
            if s.isnumeric():
                pos += int(s)
                continue
            if s == ' ':
                # TODO: this just ignores castleing and enpassant
                break


    def toFEN(self) -> str:
        """
        This function returns the FEN string of the position without the castling rights, en-passant square or move counters
        """
        pieces = 'pnbrqkPNBRQK'
        counter = 0
        fen = ''
        boardString = bin(self.getBoard())[2:]
        boardString = f'{"0"*(64-len(boardString))}{boardString}'
        for i,sq in enumerate(boardString):
            if sq == '0':
                counter += 1
            else:
                if counter > 0:
                    fen = f'{fen}{counter}'
                    counter = 0
                for k,b in enumerate(self.board):
                    if b & 2**(63-i):
                        fen = f'{fen}{pieces[k]}'
                        break
            if i % 8 == 7:
                if counter > 0:
                    fen = f'{fen}{counter}'
                    counter = 0
                fen = f'{fen}/'
        return fen[:-1]

        
    def squareToNumber(square: str) -> int:
        file = ord(square[0])-97
        rank = int(square[1])
        return 2**(63-8*(8-rank)-file)


    def squareIsEmpty(self, square: str) -> bool:
        b = self.getBoard()
        sqBin = Bitboard.squareToNumber(square)
        return not bool(b & sqBin)


    def moveToNewSquare(self, oldSquare: str, newSquare: str):
        if not self.squareIsEmpty(newSquare) or self.squareIsEmpty(oldSquare):
            return None
        osBin = Bitboard.squareToNumber(oldSquare)
        nsBin = Bitboard.squareToNumber(newSquare)
        for i,b in enumerate(self.board):
            if b & osBin:
                self.board[i] ^= osBin
                self.board[i] |= nsBin
                break
        return self


    def materialDiff(self):
        """
        This function calculates the material difference between White and Black.
        Positive numbers mean that White is up in material, negative that Black is up in material.
        """
        # P, N, B, R, Q, K
        materialValues = [1, 3, 3, 5, 9, 1000]
        whiteMaterial = 0
        blackMaterial = 0
        for i, b in enumerate(self.board):
            count = 0
            n = b
            while n > 0:
                n &= (n-1)
                count += 1
            if i < 6:
                blackMaterial += materialValues[i]*count
            else:
                whiteMaterial += materialValues[i%6]*count
        return whiteMaterial-blackMaterial


if __name__ == '__main__':
    board = Bitboard()
    board.setBoardFEN('3rnrk1/2qn1pbp/1p4p1/2p1p3/4P3/4B1PP/1PPNQPB1/R4RK1 w - - 0 18')
    board.printBoard()
    board = board.moveToNewSquare('d2', 'b5')
    board.printBoard()
    print(board.toFEN())
    board2 = Bitboard()
    board2.materialDiff()
