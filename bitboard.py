"""
Implementation of a Chess board using a 267-length bitmap to store all the data
about the chess board state.

Benchmarks:
 - PC (Ryzen 5 3600 @ 3.6 GHz, 16GB RAM)
    boardInitialization: 15.895µs
    startposMoves(50):    0.465ms
    startposMoves(100):   0.933ms
    computeLegalMoves():  3.800µs

 - Lenovo P1G4 (i7-11850H, 32GB RAM)
    boardInitialization: 13.400900003034621µs
    startposMoves(50): 0.3792362999993202ms
    startposMoves(100): 0.7665094999974826ms
"""
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
MAX_INDEX = 267
PIECE_SIZE = 4  # 4 bits for piece. piece[3] is side, and piece[0:3] is the piece
PIECE_MASK = 15 # 0b1111
CASTLES_MASK = 15 # 0b1111
ENPASSANT_MASK = 63 # 0b111111

# BITMAP INDEXES
BOARD_START = 11
SIDE_TO_MOVE_START = 10
CASTLES_START = 6

# LOGICAL CONSTANTS, MAPS AND LISTS
PIECE_MAP = {"r":ROOK, "b":BISHOP, "n":KNIGHT, "q":QUEEN}
PIECE_STRING = " prbnqk"
CASTLE_MOVES = {"e1g1":(7,7), "e8g8":(0,7), "e1c1":(7,0), "e8c8":(0,0)}
ROOK_DIRS = [(-1,0),(1,0),(0,-1),(0,1)]
BISHOP_DIRS = [(-1,-1),(-1,1),(1,-1),(1,1)]
KNIGHT_DIRS = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]
ROYAL_DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
DIR_MAP= {ROOK: ROOK_DIRS, BISHOP: BISHOP_DIRS, QUEEN: ROYAL_DIRS, \
            KNIGHT: KNIGHT_DIRS, KING: ROYAL_DIRS}

class BitBoard():
    """
    The paper said we need 768 bits? 2 x 6 x 64
    But we don't need a different bit for each piece... there are 6 possible
    pieces, so we only need 3 bits, plus one bit to represent side.

    total: 267 bits
    |  board (4x64=256 bits)  | side to move (1 bit) | castles (4 bits) | en passant (6 bits) |
    |266. . . . . . . . . . 11|10                  10|9                6|5                   0|
    """
    # TODO: move the board to the lowest bits to get rid of all the unnecessary shifts.
    def __init__(self, bits):
        assert(isinstance(bits, int))
        self._bits = bits
        self.legalMoves = None

    """ ====================== Static helper methods ======================= """
    def coordToAddress(coord):
        return BOARD_START + PIECE_SIZE * (BOARD_SIZE * coord[0] + coord[1])

    def indexToCoord(index):
        return (int(index / BOARD_SIZE), index % BOARD_SIZE)

    def indexToAlgebraic(index):
        file = "abcdefgh"[index % BOARD_SIZE]
        return file + str(8 - int(index / BOARD_SIZE))

    def algebraicToIndex(algebraic):
        return (BOARD_SIZE*(8-int(algebraic[1]))) + ord(algebraic[0])-ord('a')

    def algebraicToAddress(algebraic):
        row = 8 - int(algebraic[1])
        col = ord(algebraic[0]) - ord('a')
        return BOARD_START + PIECE_SIZE * (BOARD_SIZE * row + col)

    def algebraicToCoord(algebraic):
        return (8 - int(algebraic[1]), ord(algebraic[0]) - ord('a'))

    # Also returns an outOfBounds bool if the addition would be out of bounds
    # on a normal chess board.
    def indexPlusCoord(index, coord):
        result = index + (coord[0] * BOARD_SIZE) + coord[1]
        col = (index % BOARD_SIZE) + coord[1]
        return (result, (col < 0 or col > 7 or result < 0 or result > 63))

    # Basically only for en passant logic. Returns a 6 bit int, where the
    # higher 3 bits are for the row, and the lower 3 bits are for the col.
    def algebraicToBits(algebraic):
        return ((8 - int(algebraic[1])) << 3) + (ord(algebraic[0]) - ord('a'))

    def indexToBits(index):
        return ((8 - int(algebraic[1])) << 3) + (ord(algebraic[0]) - ord('a'))

    def pieceAtAlgebraic(bits, algebraic):
        i = BitBoard.algebraicToAddress(algebraic[0:2])
        return (bits & (PIECE_MASK << i)) >> i

    def getPiece(bits, index):
        shift = BOARD_START + PIECE_SIZE * index
        return (bits & (PIECE_MASK << shift)) >> shift

    def removePiece(bits, address):
        return bits & ~(PIECE_MASK << address)

    def addPiece(bits, address, piece):
        # Need to remove piece, if there is already a piece there
        bits = BitBoard.removePiece(bits, address)
        return bits | (piece << address)

    def pieceType(piece):
        return piece & 7

    def pieceSide(piece):
        return (piece & 8) >> 3

    def areEnemies(p1, p2):
        return BitBoard.pieceSide(p1) != BitBoard.pieceSide(p2)

    def isBackRank(index):
        return index < 8 or index >= 56

    def createFromFen(fenstring):
        fenArr = fenstring.split(" ")
        rows = fenArr[0].split("/")
        pieceMap = {"p": PAWN, "r": ROOK, "b": BISHOP, "n": KNIGHT, "q": QUEEN, "k": KING}
        bits = 0
        address = BOARD_START
        for r in range(len(rows)):
            empties = 0
            for c in range(len(rows[r])):
                if rows[r][c].isdigit():   # Empty squares
                    # empties += int(rows[r][c]) - 1
                    address += PIECE_SIZE * int(rows[r][c])
                    continue
                # Black = 0, White = 1
                player = 0 if rows[r][c].islower() else 1
                piece = (player << 3) | pieceMap[rows[r][c].lower()]
                # coord = (r, c + empties)
                bits |= piece << address
                address += PIECE_SIZE

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
        #  | index (0-64, 6 bits) |
        if (fenArr[3] != "-"):
            bits |= BitBoard.algebraicToIndex(fenArr[3])

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

    def getEnpassant(self):
        return self._bits & ENPASSANT_MASK

    def getLegalMoves(self):
        if self.legalMoves is None:
            self.computeLegalMoves()
        return self.legalMoves

    def isOpponentPiece(self, piece):
        """ Returns true if the piece is against the side to play. """
        isWhitePiece = (piece & 8) >> 3
        return isWhitePiece != self.whiteToMove()

    def isCheckMate(self):
        return False

    """ ============= Class methods ======================================== """
    def castleLogic(self, move, piece, bits):
        newCastles = self.getCastles()
        side = self.getSideToMove() << 3
        if BitBoard.pieceType(piece) == KING:
            if move in CASTLE_MOVES.keys():
                rook = CASTLE_MOVES[move]
                bits = BitBoard.removePiece(bits, BitBoard.coordToAddress(rook))
                newFile = 5 if rook[1] == 7 else 3
                rookDest = BitBoard.coordToAddress((rook[0], newFile))
                bits = BitBoard.addPiece(bits, rookDest, ROOK | self.getSideToMove())
            # Even if not castling, moving king cancels all castle possibility.
            newCastles &= ~(0b11 << (0 if self.whiteToMove() else 2))

        # If our rook moves, remove that castle possibility
        if BitBoard.pieceType(piece) == ROOK:
            shift = (2 if self.whiteToMove() else 0) + \
                    (0 if move[0] == "h" else 1)
            newCastles &= ~(0b1 << shift)

        # If we just took on a starting rook square, remove opponent's castle possibility
        oppRank = "8" if self.whiteToMove() else "1"
        if move[3] == oppRank:
            shift = (0 if self.whiteToMove() else 2) + \
                    (0 if move[2] == "h" else 1)
            newCastles &= ~(0b1 << shift)
        bits &= ((newCastles << CASTLES_START) | ~(CASTLES_MASK << CASTLES_START))
        return bits


    def makeMove(self, move):
        """
        |move| should be a string of length 4 or 5 representing the piece to be
        moved and its end location.
            <init file><init rank><dest file><dest rank>
        """
        assert(type(move) == str)
        assert(len(move) >= 4 and len(move) <= 5)

        newBits = 0
        origin = BitBoard.algebraicToAddress(move[0:2])
        piece = BitBoard.pieceAtAlgebraic(self._bits, move[0:2])

        # Right now, keep the legality checks simple and just trust in the GUI
        # to send us legal moves only.
        if piece == 0 or self.isOpponentPiece(piece):
            print("Illegal move: " + move)
            # self.prettyPrint()

        newBits = BitBoard.removePiece(self._bits, origin)
        newBits = self.castleLogic(move, piece, newBits)

        # Pawn promotion logic
        if BitBoard.pieceType(piece) == PAWN and move[3] in "18":
            if len(move) == 5:
                piece = (PIECE_MAP[move[4]] | self.getSideToMove())
            else:
                piece = (QUEEN | self.getSideToMove())

        # En passant logic
        destIndex = BitBoard.algebraicToIndex(move[2:4])
        # En passant capture
        if BitBoard.pieceType(piece) == PAWN and destIndex == self.getEnpassant():
            # captured piece is on same rank as origin, and same file as dest.
            captured = BitBoard.algebraicToAddress(move[2] + move[1])
            newBits = BitBoard.removePiece(newBits, captured)

        newBits &= ~ENPASSANT_MASK
        if BitBoard.pieceType(piece) == PAWN and move[1] in "27" and move[3] in "45":
            epRank = "3" if self.whiteToMove() else "6"
            newBits |= BitBoard.algebraicToIndex(move[0] + epRank)

        newBits = BitBoard.addPiece(newBits, BitBoard.algebraicToAddress(move[2:4]), piece)

        # Flip whose turn it is.
        newBits ^= (1 << SIDE_TO_MOVE_START)

        return BitBoard(newBits)


    """ ============== Legal Moves calculation ===================== """
    def findPiece(self, piece):
        shift = BOARD_START
        while shift < MAX_INDEX:
            if piece == ((self._bits & (PIECE_MASK << shift)) >> shift):
                return int((shift - BOARD_START) / PIECE_SIZE)
            shift += PIECE_SIZE

    def legalMovesForNonPawns(self, piece, index, directions):
        multiStep = PIECE_STRING[BitBoard.pieceType(piece)] in "rbq"
        moves = []
        src = BitBoard.indexToAlgebraic(index)
        for d in directions:
            tmp, outOfBounds = BitBoard.indexPlusCoord(index, d)
            while multiStep and not outOfBounds \
                    and BitBoard.getPiece(self._bits, tmp) == 0:
                moves.append(src + BitBoard.indexToAlgebraic(tmp))
                tmp, outOfBounds = BitBoard.indexPlusCoord(tmp, d)
            if outOfBounds:
                continue
            dest = BitBoard.getPiece(self._bits, tmp)
            if BitBoard.areEnemies(piece, dest) or \
                    (not multiStep and dest == 0):
                moves.append(src + BitBoard.indexToAlgebraic(tmp))

        return moves

    def legalMovesForPawn(self, pawn, index):
        moves = []
        src = BitBoard.indexToAlgebraic(index)
        forward = -1 if self.whiteToMove() else 1
        diagonals = [(forward, -1), (forward, 1)]
        # Pawn take logic
        for diag in diagonals:
            tmp, outOfBounds = BitBoard.indexPlusCoord(index, diag)
            if outOfBounds:
                continue
            piece = BitBoard.getPiece(self._bits, tmp)
            if piece != 0 and BitBoard.areEnemies(pawn, piece):
                if BitBoard.isBackRank(tmp):
                    [moves.append(src + BitBoard.indexToAlgebraic(tmp) + p) for p in "qrbn"]
                    continue
                moves.append(src + BitBoard.indexToAlgebraic(tmp))
                continue
            if tmp == self.getEnpassant():
                moves.append(src + BitBoard.indexToAlgebraic(tmp))

        # Pawn advance logic
        tmp, outOfBounds = BitBoard.indexPlusCoord(index, (forward, 0))
        if outOfBounds or BitBoard.getPiece(self._bits, tmp) != 0:
            return moves
        if BitBoard.isBackRank(tmp):
            [moves.append(src + BitBoard.indexToAlgebraic(tmp) + p) for p in "qrbn"]
        else:
            moves.append(src + BitBoard.indexToAlgebraic(tmp))

        # Pawn double advance logic
        if int(index / BOARD_SIZE) != (6 if self.whiteToMove() else 1):
            return moves
        double = index + (2 * BOARD_SIZE * forward)
        if BitBoard.getPiece(self._bits, double) == 0:
            moves.append(src + BitBoard.indexToAlgebraic(double))

        return moves

    def legalMovesForPiece(self, piece, index):
        if BitBoard.pieceType(piece) == PAWN:
            return self.legalMovesForPawn(piece, index)
        return self.legalMovesForNonPawns(piece, index, \
            DIR_MAP[BitBoard.pieceType(piece)])

    def legalCastleMoves(self):
        castleMap = {0b0001: "e8g8",  # k (black king-side)
                    0b0010: "e8c8",  # q (black queen-side)
                    0b0100: "e1g1",  # K (white king-side)
                    0b1000: "e1c1"}  # Q (white queen-side)
        moves = []
        for shift in range(2):
            mask = 1 << (shift + (2 if self.whiteToMove() else 0))
            castle = self.getCastles() & mask
            if castle == 0:
                continue
            isKingside = (shift == 0)
            # Check squares between king and rook
            emptyMask = 255 if isKingside else 4095
            shift = BOARD_START + (56 * 4 if self.whiteToMove() else 0) \
                    + (20 if isKingside else 4)
            if (self._bits & (emptyMask << shift)) != 0:
                continue

            # Check that all transit squares are not attacked
            transits = [2,3,4] if self.whiteToMove() else [4,5,6]
            row = 56 if self.whiteToMove() else 0
            if any([self.isSquareAttacked(t + row, (self.getSideToMove() | KING)) \
                    for t in transits]):
                continue
            moves.append(castleMap[castle])
        return moves


    def isSquareAttackedByPiece(self, index, target, directions, pieces):
        multiStep = any([p in pieces for p in "rbq"])
        for d in directions:
            tmp, outOfBounds = BitBoard.indexPlusCoord(index, d)
            while multiStep and not outOfBounds \
                    and BitBoard.getPiece(self._bits, tmp) == 0:
                tmp, outOfBounds = BitBoard.indexPlusCoord(tmp, d)
            if outOfBounds:
                continue
            piece = BitBoard.getPiece(self._bits, tmp)
            pieceStr = PIECE_STRING[BitBoard.pieceType(piece)]
            if pieceStr in pieces and BitBoard.areEnemies(piece, target):
                return True
        return False

    def isSquareAttacked(self, index, target = None):
        """
        If target is None, will use whatever piece is at the index.
        """
        directionals = [(KNIGHT_DIRS, "n"), (ROOK_DIRS, "rq"), \
                        (BISHOP_DIRS, "bq"), (ROYAL_DIRS, "k")]
        if target is None:
            target = BitBoard.getPiece(self._bits, index)
        if any([self.isSquareAttackedByPiece(index, target, dir, ps) \
                for (dir, ps) in directionals]):
            return True
        # Pawn logic is special
        forward = 1 if self.whiteToMove() else -1
        diagonals = [(forward, 1), (forward, -1)]
        for diag in diagonals:
            tmp, outOfBounds = BitBoard.indexPlusCoord(index, diag)
            if outOfBounds:
                continue
            piece = BitBoard.getPiece(self._bits, tmp)
            if BitBoard.pieceType(piece) == PAWN and BitBoard.areEnemies(piece, target):
                return True
        return False

    def isKingSafeAfterMove(self, move):
        postMoveBoard = self.makeMove(move)
        king = self.getSideToMove() | KING
        kingIndex = postMoveBoard.findPiece(king)
        # print(move)
        # postMoveBoard.prettyPrint()
        return not postMoveBoard.isSquareAttacked(kingIndex, king)

    def computeLegalMoves(self):
        if self.legalMoves is not None:
            return
        moves = []
        for i in range(BOARD_SIZE * BOARD_SIZE):
            piece = BitBoard.getPiece(self._bits, i)
            if piece == 0 or self.isOpponentPiece(piece):
                continue
            moves += filter(self.isKingSafeAfterMove, \
                        self.legalMovesForPiece(piece, i))
        moves += self.legalCastleMoves()
        self.legalMoves = moves

    """ ============== Debugging and Printing ===================== """
    def prettyPrint(self):
        for i in range(BOARD_SIZE * BOARD_SIZE):
            if i % BOARD_SIZE == 0:
                print("|", end='')
            bitmask = 15 << (i * PIECE_SIZE + BOARD_START)
            pieceBits = (self._bits & bitmask) >> (i * PIECE_SIZE + BOARD_START)
            piece = PIECE_STRING[pieceBits & 7]
            whiteToPlay = pieceBits & 8
            piece = piece.upper() if whiteToPlay else piece
            if i % BOARD_SIZE != 0:
                print(piece.rjust(2), end='')
            else:
                print(piece, end='')
            if i % BOARD_SIZE == 7:
                print("|")

    def prettyPrintVerbose(self):
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
        self.prettyPrint()
        print()

if __name__ == "__main__":
    board = BitBoard.createFromFen(STARTING_FEN)
    board.prettyPrint()
    board = board.makeMove("b1c3")
    board = board.makeMove("b8f3")
    board = board.makeMove("c1a3")
    board = board.makeMove("c8a6")
    board = board.makeMove("d1d3")
    board = board.makeMove("d8d6")
    board.prettyPrintVerbose()
    # board = board.makeMove("e5f6")
    # board.prettyPrintVerbose()
    print(board.getLegalMoves())
