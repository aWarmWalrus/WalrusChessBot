from copy import deepcopy
import random
from collections import defaultdict

ENGINE_NAME = "ARYA"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "r1b1k1nr/p2p1pNp/n1B5/1p1NPR1P/6P1/3P1Q2/P1P1K3/qR4b1 b KQkq - 1 2"
BOARD_SIZE = 8
ROOK_DIRS = [(-1,0),(1,0),(0,-1),(0,1)]
BISHOP_DIRS = [(-1,-1),(-1,1),(1,-1),(1,1)]
KNIGHT_DIRS = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]
ROYAL_DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

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

def areEnemies(piece1, piece2):
    return piece1.isupper() != piece2.isupper()

def outOfBounds(coord):
    return coord[0] < 0 or coord[0] > 7 or coord[1] < 0 or coord[1] > 7

def findPiece(piece, board):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == piece:
                return (r,c)

class Array2DBoard:
    def __init__(self, board = None, whiteToPlay = True):
        if board is None:
            self.board = [[" " for _ in range(8)] for _ in range(8)]
        else:
            assert(isinstance(board, list))
            assert(len(board) == 8)
            assert(len(board[0]) == 8)
            self.board = deepcopy(board)
        self.whiteToPlay = whiteToPlay

    # TODO: handle castling logic.
    def setPositionWithFen(self, fen):
        fenArr = fen.split(" ")
        self.whiteToPlay = True if fenArr[1] == "w" else False

        rows = fenArr[0].split("/")
        for r in range(len(rows)):
            empties = 0
            for c in range(len(rows[r])):
                if rows[r][c].isdigit():
                    for cp in range(int(rows[r][c])):
                        self.board[r][c + empties + cp] = " "
                    empties += int(rows[r][c]) - 1
                    continue
                self.board[r][c + empties] = rows[r][c]


    def makeMove(self, move):
        """
        |move| should be a string of length 4 or 5 representing the piece to be
        moved and its end location.
        """
        assert(type(move) == str)
        assert(len(move) >= 4 and len(move) <= 5)
        colMap = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7}

        piece = self.board[8-int(move[1])][colMap[move[0]]]

        # Right now, keep the legality checks simple and just trust in the GUI
        # to send us legal moves only.
        if piece == " ":
            print("Illegal move: " + move)
            self.prettyPrint()
        # TODO: handle the following cases
        #  - en passant
        #  - castling
        #  - pawn promotion
        self.board[8-int(move[1])][colMap[move[0]]] = " "
        self.board[8-int(move[3])][colMap[move[2]]] = piece
        return Array2DBoard(self.board, not self.whiteToPlay)

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
                moves.append(init + coordToAlgebraic(diag))

        # Single step forward logic
        oneStep = (coord[0] + forward, coord[1])
        if outOfBounds(oneStep) or self.board[oneStep[0]][oneStep[1]] != " ":
            # If one step forward is out of bounds or blocked, two steps foward
            # would be as well.
            return moves
        moves.append(init + coordToAlgebraic(oneStep))

        # Double step forward logic
        baseRow = 6 if self.whiteToPlay else 1
        if coord[0] != baseRow:
            return moves
        doubleStep = (coord[0] + forward * 2, coord[1])
        if outOfBounds(doubleStep) or \
                self.board[doubleStep[0]][doubleStep[1]] != " ":
            return moves
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


    def isKingSafe(self, move):
        """
        Returns false if the move causes board to be in a state in which the
        active player's king is in check.
        """
        king = "K" if self.whiteToPlay else "k"
        kCoord = findPiece(king, self.board)
        # TODO: implement this method
        return True


    def legalMoves(self):
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
            legalMoves += filter(self.isKingSafe, self.legalMovesForPiece(piece, (r, c)))
        return legalMoves

    def prettyPrint(self):
        print(" _ _ _ _ _ _ _ _")
        for row in self.board:
            print ("|" + "|".join(row) + "|")


class Engine:
    def __init__(self):
        self.options = defaultdict(str)
        self.board = Array2DBoard()

    def inputUCI(self):
        print("id name " + ENGINE_NAME)
        print("id author Walrus")
        print("uciok")

    def setOptions(self, line):
        print("unimplemented")

    def isReady(self):
        print("readyok")

    def newGame(self):
        pass  # nothing to do

    def position(self, line):
        words = line.split()
        assert(words[0] == "position")

        if words[1] == "startpos":
            self.board.setPositionWithFen(STARTING_FEN)
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self.board = self.board.makeMove(move)
                    self.board.prettyPrint()
        else:
            print("weird " + words.join())

    def go(self):
        moves = self.board.legalMoves()
        print("bestmove " + random.choice(moves))

    def run(self):
        while True:
            line = input()
            if line == "uci":
                self.inputUCI()
            elif line.startswith("setoption"):
                self.setOptions(line)
            elif line.startswith("isready"):
                self.isReady()
            elif line.startswith("ucinewgame"):
                self.newGame()
            elif line.startswith("position"):
                self.position(line)
            elif line.startswith("go"):
                self.go()
            elif line.startswith("print"):
                self.board.prettyPrint()
                print(self.board.legalMoves())
            elif line.startswith("end"):
                print("goodbye")
                break

engine = Engine()
engine.run()
