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


    def printBoard(self):
        b = 0x0
        for piece in self.board:
            b = b | piece
        for i in range(8):
            print(bin(b)[2:][i*8:(i+1)*8])


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


if __name__ == '__main__':
    board = Bitboard()
    board.printBoard()
    board.setBoardFEN('rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2')
    board.printBoard()
