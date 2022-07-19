"""
Chess board implemented using a simple 2D array of strings. Very efficient. I
know...

Benchmarks:
 - PC (Ryzen 5 3600 @ 3.6 GHz, 16GB RAM)
    boardInitialization: 12.857µs
    startposMoves(50):    3.023ms
    startposMoves(100):   6.035ms
    computeLegalMoves():  5.236µs

 - Lenovo P1G4 (i7-11850H, 32GB RAM)
    boardInitialization: 10.040400000434602µs
    startposMoves(50): 2.1606331000002683ms
    startposMoves(100): 4.414085200001864ms
"""
from copy import deepcopy

BOARD_SIZE = 8
ROOK_DIRS = [(-1,0),(1,0),(0,-1),(0,1)]
BISHOP_DIRS = [(-1,-1),(-1,1),(1,-1),(1,1)]
KNIGHT_DIRS = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]
ROYAL_DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
CASTLE_MOVES = {"e1g1":(7,7), "e8g8":(0,7), "e1c1":(7,0), "e8c8":(0,0)}

def colToFile(colNum):
    col = int(colNum) if type(colNum) == str else colNum
    return "abcdefgh"[col]

def coordToAlgebraic(coord):
    """
    Assumes |coord| is a 2D tuple of ints, representing (row, column).
    Note that this flips the order of row and column because algebraic notation
    is formatted as <file><rank> (col then row).
    """
    return colToFile(coord[1]) + str(8 - coord[0])

def algebraicToCoord(algebraic):
    colMap = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}
    return (8 - int(algebraic[1]), colMap[algebraic[0]])

def areEnemies(piece1, piece2):
    return piece1.isupper() != piece2.isupper()

def outOfBounds(coord):
    return coord[0] < 0 or coord[0] > 7 or coord[1] < 0 or coord[1] > 7

def findPiece(piece, board):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == piece:
                return (r,c)

class Array2DBoard():
    def __init__(self, board, whiteToPlay, castles, enpassant):
        """
        Params:
            castles: a 0-4 length string matching the FEN specs.
            enpassant: a 2 length string of the algebraic square that a pawn
                       is allowed to en passant on to, if any are. If not, then
                       simply should be empty.
        """
        assert(isinstance(board, list))
        assert(len(board) == BOARD_SIZE)
        assert(len(board[0]) == BOARD_SIZE)
        self.board = board
        self.whiteToPlay = whiteToPlay
        self.castles = castles
        self.enpassant = enpassant
        self.legalMoves = None

    def isOpponentPiece(self, piece):
        return piece.isupper() != self.whiteToPlay

    def createFromFen(fen):
        fenArr = fen.split(" ")
        whiteToPlay = True if fenArr[1] == "w" else False
        board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        rows = fenArr[0].split("/")
        for r in range(len(rows)):
            empties = 0
            for c in range(len(rows[r])):
                if rows[r][c].isdigit():
                    for cp in range(int(rows[r][c])):
                        board[r][c + empties + cp] = " "
                    empties += int(rows[r][c]) - 1
                    continue
                board[r][c + empties] = rows[r][c]
        castles = fenArr[2]
        enpassant = fenArr[3]
        return Array2DBoard(board, whiteToPlay, castles, enpassant)

    def castleLogic(self, move, piece, board):
        newCastles = self.castles
        if piece.lower() == "k":
            if move in CASTLE_MOVES.keys():
                rook = CASTLE_MOVES[move]
                board[rook[0]][rook[1]] = " "
                newFile = 5 if rook[1] == 7 else 3
                board[rook[0]][newFile] = "R" if self.whiteToPlay else "r"
            # Even if not castling, moving king cancels all castle possibility.
            newCastles = newCastles.replace("K" if self.whiteToPlay else "k", "")
            newCastles = newCastles.replace("Q" if self.whiteToPlay else "q", "")

        # If our rook moves, remove that castle possibility
        if piece.lower() == "r":
            if move[0] == "a":
                newCastles = newCastles.replace("Q" if self.whiteToPlay else "q", "")
            elif move[0] == "h":
                newCastles = newCastles.replace("K" if self.whiteToPlay else "k", "")

        # If we just took on a starting rook square, remove opponent's castle possibility
        oppRank = "8" if self.whiteToPlay else "1"
        if move[3] == oppRank:
            if move[2] == "h":
                newCastles = newCastles.replace("k" if self.whiteToPlay else "K", "")
            elif move[2] == "a":
                newCastles = newCastles.replace("q" if self.whiteToPlay else "Q", "")
        return newCastles

    def makeMove(self, move):
        """
        |move| should be a string of length 4 or 5 representing the piece to be
        moved and its end location.
            <init file><init rank><dest file><dest rank>
        """
        assert(type(move) == str)
        assert(len(move) >= 4 and len(move) <= 5)

        newBoard = deepcopy(self.board)
        origin = algebraicToCoord(move[0:2])
        piece = newBoard[origin[0]][origin[1]]

        # Right now, keep the legality checks simple and just trust in the GUI
        # to send us legal moves only.
        if piece == " " or piece.isupper() != self.whiteToPlay:
            print("Illegal move: " + move)
            self.prettyPrint()
        newBoard[origin[0]][origin[1]] = " "

        newCastles = self.castleLogic(move, piece, newBoard)

        # Pawn promotion logic
        if piece.lower() == "p" and move[3] in "18":
            if len(move) == 5:
                piece = move[4].upper() if self.whiteToPlay else move[4].lower()
            else:
                piece = "Q" if self.whiteToPlay else "q"

        # En passant logic
        dest = algebraicToCoord(move[2:4])
        if piece.lower() == "p" and move[2:4] == self.enpassant: # Capture
            # captured piece is on same rank as origin, and same file as dest.
            captured = algebraicToCoord(move[2] + move[1])
            newBoard[captured[0]][captured[1]] = " "
        newEnpassant = ""
        if piece.lower() == "p" and move[1] in "27" and move[3] in "45":
            epRank = "3" if self.whiteToPlay else "6"
            newEnpassant = move[0] + epRank

        newBoard[dest[0]][dest[1]] = piece
        return Array2DBoard(newBoard, not self.whiteToPlay, newCastles, newEnpassant)

    def legalMovesForLinearMover(self, piece, coord, directions):
        moves = []
        init = coordToAlgebraic((coord[0], coord[1]))
        for d in directions:
            tmp = (coord[0] + d[0], coord[1] + d[1])
            while not outOfBounds(tmp) and self.board[tmp[0]][tmp[1]] == " ":
                moves.append(init + coordToAlgebraic(tmp))
                tmp = (tmp[0] + d[0], tmp[1] + d[1])
            if not outOfBounds(tmp) and areEnemies(self.board[tmp[0]][tmp[1]], piece):
                moves.append(init + coordToAlgebraic(tmp))
        return moves

    def legalMovesForPawn(self, piece, coord):
        moves = []
        init = coordToAlgebraic((coord[0], coord[1]))
        forward = -1 if self.whiteToPlay else 1

        # Diagonal take logic
        diagonalTakes = [(coord[0] + forward, coord[1] - 1), \
                         (coord[0] + forward, coord[1] + 1)]
        for diag in diagonalTakes:
            if outOfBounds(diag):
                continue
            destPiece = self.board[diag[0]][diag[1]]
            if destPiece != " " and areEnemies(piece, destPiece):
                if diag[0] in [0, 7]:  # pawn promotion
                    [moves.append(init + coordToAlgebraic(diag) + p) for p in "qrbn"]
                else:
                    moves.append(init + coordToAlgebraic(diag))
                continue
            enPassant = coordToAlgebraic(diag)
            if enPassant == self.enpassant:
                moves.append(init + self.enpassant)

        # Single step forward logic
        oneStep = (coord[0] + forward, coord[1])
        if outOfBounds(oneStep) or self.board[oneStep[0]][oneStep[1]] != " ":
            return moves
        if oneStep[0] in [0, 7]: # pawn promotion
            [moves.append(init + coordToAlgebraic(oneStep) + p) for p in "qrbn"]
        else:
            moves.append(init + coordToAlgebraic(oneStep))

        # Double step forward logic
        baseRow = 6 if self.whiteToPlay else 1
        if coord[0] != baseRow:
            return moves
        doubleStep = (coord[0] + forward * 2, coord[1])
        if self.board[doubleStep[0]][doubleStep[1]] == " ":
            moves.append(init + coordToAlgebraic(doubleStep))
        return moves


    def legalMovesForPiece(self, piece, coord):
        init = coordToAlgebraic((coord[0], coord[1]))
        if piece.lower() == "p": # Pawns
            return self.legalMovesForPawn(piece, coord)
        elif piece.lower() == "r": # Rooks
            return self.legalMovesForLinearMover(piece, coord, ROOK_DIRS)
        elif piece.lower() == "b": # Bishops
            return self.legalMovesForLinearMover(piece, coord, BISHOP_DIRS)
        elif piece.lower() == "n": # Knights
            moves = []
            for d in KNIGHT_DIRS:
                tmp = (coord[0] + d[0], coord[1] + d[1])
                if outOfBounds(tmp):
                    continue
                targetPiece = self.board[tmp[0]][tmp[1]]
                if targetPiece == " " or areEnemies(targetPiece, piece):
                    moves.append(init + coordToAlgebraic(tmp))
            return moves
        elif piece.lower() == "q":  # Queens
            return self.legalMovesForLinearMover(piece, coord, ROYAL_DIRS)
        elif piece.lower() == "k":  # Kings
            moves = []
            for d in ROYAL_DIRS:
                tmp = (coord[0] + d[0], coord[1] + d[1])
                if outOfBounds(tmp):
                    continue
                targetPiece = self.board[tmp[0]][tmp[1]]
                if targetPiece == " " or areEnemies(targetPiece, piece):
                    moves.append(init + coordToAlgebraic(tmp))
            return moves
        raise Exception("unknown piece on the board: " + piece)

    def isSquareAttackedByPiece(self, board, coord, directions, pieces):
        # multiStep means that |pieces| can move multiple tiles in one move. All
        # except the King, Pawns and Knights are regarded as multistep.
        multiStep = any([p in pieces for p in "rbq"])

        for d in directions:
            tmp = (coord[0] + d[0], coord[1] + d[1])
            while multiStep and not outOfBounds(tmp) and board[tmp[0]][tmp[1]] == " ":
                tmp = (tmp[0] + d[0], tmp[1] + d[1])
            if outOfBounds(tmp):
                continue
            piece = board[tmp[0]][tmp[1]]
            if piece.lower() in pieces and self.isOpponentPiece(piece):
                return True
        return False

    def isSquareAttacked(self, board, coord):
        # Check for enemy knights
        if self.isSquareAttackedByPiece(board, coord, KNIGHT_DIRS, "n") or \
                self.isSquareAttackedByPiece(board, coord, ROOK_DIRS, "rq") or \
                self.isSquareAttackedByPiece(board, coord, BISHOP_DIRS, "bq") or \
                self.isSquareAttackedByPiece(board, coord, ROYAL_DIRS, "k"):
            return True
        # Check for enemy pawns
        forward = -1 if self.whiteToPlay else 1
        diagonalTakes = [(coord[0] + forward, coord[1] + 1), \
                        (coord[0] + forward, coord[1] - 1)]
        for diag in diagonalTakes:
            if outOfBounds(diag):
                continue
            piece = board[diag[0]][diag[1]]
            if piece.lower() == "p" and self.isOpponentPiece(piece):
                return True
        return False

    def isKingSafeAfterMove(self, move):
        king = "K" if self.whiteToPlay else "k"
        newBoard = self.makeMove(move).board
        return not self.isSquareAttacked(newBoard, findPiece(king, newBoard))

    def legalCastleMoves(self):
        legalCastles = {"Q":"e1c1", "K":"e1g1", "q":"e8c8", "k":"e8g8"}
        moves = []
        for c in self.castles:
            if self.isOpponentPiece(c):
                continue
            row = 7 if self.whiteToPlay else 0
            # if the squares between the king and rook are empty
            empties = [5,6] if c.lower() == "k" else [1,2,3]
            unattacked = [4,5,6] if c.lower() == "k" else [2,3,4]
            if any([self.board[row][col] != " " for col in empties]):
                continue
            if any([self.isSquareAttacked(self.board, (row, col)) for col in unattacked]):
                continue
            moves.append(legalCastles[c])
        return moves

    def getLegalMoves(self):
        if self.legalMoves is not None:
            return self.legalMoves
        self.computeLegalMoves()
        return self.legalMoves

    def computeLegalMoves(self):
        if self.legalMoves is not None:
            return
        allPieces = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                piece = self.board[r][c]
                if piece == " ":
                    continue
                if piece.isupper() and self.whiteToPlay:
                    allPieces.append((piece, r, c))
                elif piece.islower() and not self.whiteToPlay:
                    allPieces.append((piece, r, c))
        legalMoves = []
        for piece, r, c in allPieces:
            legalMoves += filter(self.isKingSafeAfterMove, \
                            self.legalMovesForPiece(piece, (r, c)))
        legalMoves += self.legalCastleMoves()
        self.legalMoves = legalMoves

    def isCheckMate(self):
        king = "K" if self.whiteToPlay else "k"
        return len(self.legalMoves) == 0 and \
            self.isSquareAttacked(self.board, findPiece(king, self.board))

    def prettyPrint(self):
        print(" _ _ _ _ _ _ _ _")
        for row in self.board:
            print ("|" + "|".join(row) + "|")
