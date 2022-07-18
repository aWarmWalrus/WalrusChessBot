
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "r1b1k1nr/p2p1pNp/n1B5/1p1NPR1P/6P1/3P1Q2/P1P1K3/qR4b1 b KQkq - 1 2"

EMPTY = 0
PAWN = 1
ROOK = 2
BISHOP = 3
KNIGHT = 4
QUEEN = 5
KING = 6

BOARD_SIZE = 8
PIECE_SIZE = 4  # 4 bits for piece. piece[3] is side, and piece[0:3] is the piece
PIECE_MASK = 15 # 0b1111
CASTLES_MASK = 15 # 0b1111

# BITMAP INDEXES
BOARD_START = 11
SIDE_TO_MOVE_START = 10
CASTLES_START = 6

# LOGICAL CONSTANTS, MAPS AND LISTS
PIECE_MAP = {"r":ROOK, "b":BISHOP, "n":KNIGHT, "q":QUEEN}
CASTLE_MOVES = {"e1g1":(7,7), "e8g8":(0,7), "e1c1":(7,0), "e8c8":(0,0)}

class BitBoard():
    """
    The paper said we need 768 bits? 2 x 6 x 64
    But we don't need a different bit for each piece... there are 6 possible
    pieces, so we only need 3 bits, plus one bit to represent side.

    total: 267 bits
    |  board (4x64=256 bits)  | side to move (1 bit) | castles (4 bits) | en passant (6 bits) |
    |266. . . . . . . . . . 11|10                  10|9                6|5                   0|
    """
    def __init__(self, bits):
        assert(isinstance(bits, int))
        self._bits = bits

    """ ====================== Static helper methods ======================= """
    def coordToIndex(coord):
        return BOARD_START + PIECE_SIZE * (BOARD_SIZE * coord[0] + coord[1])

    def indexToCoord(index):
        return (int(index / BOARD_SIZE), index % BOARD_SIZE)

    def algebraicToIndex(algebraic):
        row = 8 - int(algebraic[1])
        col = ord(algebraic[0]) - ord('a')
        return BOARD_START + PIECE_SIZE * (BOARD_SIZE * row + col)

    def algebraicToCoord(algebraic):
        return (8 - int(algebraic[1]), ord(algebraic[0]) - ord('a'))

    def pieceAtAlgebraic(bits, algebraic):
        i = BitBoard.algebraicToIndex(algebraic[0:2])
        return (bits & (PIECE_MASK << i)) >> i

    def removePiece(bits, index):
        return bits & ~(PIECE_MASK << index)

    def addPiece(bits, index, piece):
        # Need to remove piece, if there is already a piece there
        bits = BitBoard.removePiece(bits, index)
        return bits | (piece << index)

    def pieceType(piece):
        return piece & 7

    def pieceSide(piece):
        return (piece & 8) >> 3

    def createFromFen(fenstring):
        fenArr = fenstring.split(" ")
        rows = fenArr[0].split("/")
        pieceMap = {"p": PAWN, "r": ROOK, "b": BISHOP, "n": KNIGHT, "q": QUEEN, "k": KING}
        bits = 0
        for r in range(len(rows)):
            empties = 0
            for c in range(len(rows[r])):
                if rows[r][c].isdigit():   # Empty squares
                    empties += int(rows[r][c]) - 1
                    continue
                # Black = 0, White = 1
                player = 0 if rows[r][c].islower() else 1
                piece = (player << 3) | pieceMap[rows[r][c].lower()]
                coord = (r, c + empties)
                bits |= piece << BitBoard.coordToIndex(coord)

        # SIDE TO MOVE: 0 is black, 1 is white
        if fenArr[1] == "w":
            bits |= 1 << SIDE_TO_MOVE_START

        # CASTLES:
        #   k (black king-side):  0  (0b00)
        #   q (black queen-side): 1  (0b01)
        #   K (white king-side):  2  (0b10)
        #   Q (white queen-side): 3  (0b11)
        castles = 0
        for castle in fenArr[2]:
            tmp = 1 if castle.islower() else 4
            if castle.lower() == "k":
                castles |= tmp
            elif castle.lower() == "q":
                castles |= tmp << 1
        bits |= castles << CASTLES_START

        # EN PASSANT:
        #  | row (0-7, 3 bits) | col (0-7, 3 bits) |
        if (fenArr[3] != "-"):
            coord = BitBoard.algebraicToCoord(fenArr[3])
            bits |= (coord[0] << 3) + coord[1]

        return BitBoard(bits)

    """ Getters """
    def getCastles(self):
        return (self._bits & (CASTLES_MASK << CASTLES_START)) >> CASTLES_START

    # This is more useful as syntactic sugar for if statements.
    def whiteToMove(self):
        return (self._bits & (1 << SIDE_TO_MOVE_START)) >> SIDE_TO_MOVE_START

    # This is more useful when creating a piece.
    def getSideToMove(self):
        # 10 (SIDE_TO_MOVE_START) - 3 (PIECE BITS)
        return (self._bits & (1 << SIDE_TO_MOVE_START)) >> 7

    def isOpponentPiece(self, piece):
        """ Returns true if the piece is against the side to play. """
        isWhitePiece = (piece & 8) >> 3
        return isWhitePiece != self.whiteToMove()

    """ ============= Class methods ======================================== """
    def castleLogic(self, move, piece, bits):
        newCastles = self.getCastles()
        side = self.getSideToMove() << 3
        if BitBoard.pieceType(piece) == KING:
            if move in CASTLE_MOVES.keys():
                rook = CASTLE_MOVES[move]
                bits = BitBoard.removePiece(bits, BitBoard.coordToIndex(rook))
                newFile = 5 if rook[1] == 7 else 3
                rookDest = BitBoard.coordToIndex(rook[0], newFile)
                bits = BitBoard.addPiece(bits, rookDest, ROOK | self.getSideToMove())
            # Even if not castling, moving king cancels all castle possibility.
            newCastles &= ~(0b11 << (0 if self.whiteToMove() else 2))

        # If our rook moves, remove that castle possibility
        if BitBoard.pieceType(piece) == ROOK:
            shift = (2 if self.whiteToMove() else 0) + \
                    (0 if move[0] == "h" else 1)
            newCastles &= ~(0b1 << shift)

        # If we just took on a starting rook square, remove opponent's castle possibility
        # oppRank = "8" if self.whiteToPlay else "1"
        # if move[3] == oppRank:
        #     if move[2] == "h":
        #         newCastles = newCastles.replace("k" if self.whiteToPlay else "K", "")
        #     elif move[2] == "a":
        #         newCastles = newCastles.replace("q" if self.whiteToPlay else "Q", "")
        return newCastles


    def makeMove(self, move):
        """
        |move| should be a string of length 4 or 5 representing the piece to be
        moved and its end location.
            <init file><init rank><dest file><dest rank>
        """
        assert(type(move) == str)
        assert(len(move) >= 4 and len(move) <= 5)

        newBits = 0
        origin = BitBoard.algebraicToIndex(move[0:2])
        piece = BitBoard.pieceAtAlgebraic(self._bits, move[0:2])

        # Right now, keep the legality checks simple and just trust in the GUI
        # to send us legal moves only.
        if piece == 0 or self.isOpponentPiece(piece):
            print("Illegal move: " + move)
            # self.prettyPrint()

        newBits = BitBoard.removePiece(self._bits, origin)
        newCastles = self.castleLogic(move, piece, newBits)
        newBits &= ((newCastles << CASTLES_START) | ~(CASTLES_MASK << CASTLES_START))

        # Pawn promotion logic
        if BitBoard.pieceType(piece) == PAWN and move[3] in "18":
            if len(move) == 5:
                piece = (PIECE_MAP[move[4]] | self.getSideToMove())
            else:
                piece = (QUEEN | self.getSideToMove())

        # En passant logic
        dest = BitBoard.algebraicToIndex(move[2:4])
        # if piece.lower() == "p" and move[2:4] == self.enpassant: # Capture
        #     # captured piece is on same rank as origin, and same file as dest.
        #     captured = algebraicToCoord(move[2] + move[1])
        #     newBoard[captured[0]][captured[1]] = " "
        # newEnpassant = ""
        # if piece.lower() == "p" and move[1] in "27" and move[3] in "45":
        #     epRank = "3" if self.whiteToPlay else "6"
        #     newEnpassant = move[0] + epRank
        #
        newBits = BitBoard.addPiece(newBits, dest, piece)

        # Flip whose turn it is.
        newBits ^= (1 << SIDE_TO_MOVE_START)

        return BitBoard(newBits)



    def prettyPrint(self):
        print("PRETTY PRINT ==================")
        print("Board bits as int: {}".format(self._bits))
        binary = format(self._bits, '#0269b')
        print("Board bits binary: " + binary)
        print("  Board [11:267]: (is reflected across x=y compared to normal board)")
        strStart = 2
        for i in range(BOARD_SIZE):
            start = strStart + i * PIECE_SIZE * BOARD_SIZE
            end = strStart + (i + 1) * PIECE_SIZE * BOARD_SIZE
            print("    {}".format(binary[start:end]))
        side_to_play = strStart + (BOARD_SIZE * BOARD_SIZE * PIECE_SIZE)
        print("  Side to move[10]: {}".format(binary[side_to_play]))
        castles = side_to_play + 1
        print("  Castles[6:10]: {}".format(binary[castles:castles+4]))
        print("  En Passant[0:6]: {}\n".format(binary[castles+4:castles+10]))

        print("Board (fancy): \n")
        pieceStr = " prbnqk"
        for i in range(BOARD_SIZE * BOARD_SIZE):
            if i % BOARD_SIZE == 0:
                print("|", end='')
            bitmask = 15 << (i * PIECE_SIZE + BOARD_START)
            pieceBits = (self._bits & bitmask) >> (i * PIECE_SIZE + BOARD_START)
            piece = pieceStr[pieceBits & 7]
            whiteToPlay = pieceBits & 8
            piece = piece.upper() if whiteToPlay else piece
            if i % BOARD_SIZE != 0:
                print(piece.rjust(2), end='')
            else:
                print(piece, end='')
            if i % BOARD_SIZE == 7:
                print("|")
        print()

if __name__ == "__main__":
    board = BitBoard.createFromFen(STARTING_FEN)
    board.prettyPrint()
    board = board.makeMove("a1a4")
    board.prettyPrint()
    board = board.makeMove("a8a6")
    board.prettyPrint()
    board = board.makeMove("h1h4")
    board.prettyPrint()
