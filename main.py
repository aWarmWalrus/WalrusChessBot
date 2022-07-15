from collections import defaultdict

ENGINE_NAME = "ARYA"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "r1b1k1nr/p2p1pNp/n1B5/1p1NPR1P/6P1/3P1Q2/P1P1K3/qR4b1 b KQkq - 1 2"

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

class Array2DBoard:
    def __init__(self):
        self.board = [[" " for _ in range(8)] for _ in range(8)]
        self.whiteToPlay = True

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


    def updateWithMove(self, move):
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
        self.whiteToPlay = not self.whiteToPlay

    def legalMovesForLinearMover(self, piece, coord, board, directions):
        moves = []
        init = coordToAlgebraic((coord[0], coord[1]))
        for d in directions:
            tmp = (coord[0] + d[0], coord[1] + d[1])
            while not outOfBounds(tmp) and board[tmp[0]][tmp[1]] == " ":
                moves.append(init + coordToAlgebraic(tmp))
                tmp = (tmp[0] + d[0], tmp[1] + d[1])
            if not outOfBounds(tmp) and areEnemies(board[tmp[0]][tmp[1]], piece):
                moves.append(init + coordToAlgebraic(tmp))
        return moves

    def legalMovesForPiece(self, piece, coord, board):
        moves = []
        init = coordToAlgebraic((coord[0], coord[1]))
        match piece.lower():
            case "p":  # Pawns
                forward = -1 if self.whiteToPlay else 1

                # Diagonal take logic
                diagonalTakes = [(coord[0] + forward, coord[1] - 1), \
                                 (coord[0] + forward, coord[1] + 1)]
                for diag in diagonalTakes:
                    if outOfBounds(diag):
                        continue
                    destPiece = board[diag[0]][diag[1]]
                    if destPiece != " " and areEnemies(piece, destPiece):
                        moves.append(init + coordToAlgebraic(diag))

                # Single step forward logic
                oneStep = (coord[0] + forward, coord[1])
                if outOfBounds(oneStep) or board[oneStep[0]][oneStep[1]] != " ":
                    # If one step is out of bounds or blocked, it will be true
                    # with two steps too.
                    return moves
                moves.append(init + coordToAlgebraic(oneStep))

                # Double step forward logic
                baseRow = 6 if self.whiteToPlay else 1
                if coord[0] != baseRow:
                    return moves
                doubleStep = (coord[0] + forward * 2, coord[1])
                if outOfBounds(doubleStep) or \
                        board[doubleStep[0]][doubleStep[1]] != " ":
                    return moves
                moves.append(init + coordToAlgebraic(doubleStep))
                return moves
            case "r":
                directions = [(-1,0),(1,0),(0,-1),(0,1)]
                return self.legalMovesForLinearMover(piece, coord, board, directions)
            case "b":
                directions = [(-1,-1),(1,1),(1,-1),(-1,1)]
                return self.legalMovesForLinearMover(piece, coord, board, directions)
            case "n":
                directions = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]
                for d in directions:
                    tmp = (coord[0] + d[0], coord[1] + d[1])
                    if outOfBounds(tmp):
                        continue
                    targetPiece = board[tmp[0]][tmp[1]]
                    if targetPiece == " " or areEnemies(targetPiece, piece):
                        moves.append(init + coordToAlgebraic(tmp))
                return moves
            case "q":
                directions = [(-1,-1),(1,1),(1,-1),(-1,1), \
                              (-1,0),(1,0),(0,-1),(0,1)]
                return self.legalMovesForLinearMover(piece, coord, board, directions)
            case "k":
                directions = [(-1,-1),(1,1),(1,-1),(-1,1), \
                              (-1,0),(1,0),(0,-1),(0,1)]
                for d in directions:
                    tmp = (coord[0] + d[0], coord[1] + d[1])
                    if outOfBounds(tmp):
                        continue
                    targetPiece = board[tmp[0]][tmp[1]]
                    if targetPiece == " " or areEnemies(targetPiece, piece):
                        moves.append(init + coordToAlgebraic(tmp))
                return moves
        return moves


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
            legalMoves += self.legalMovesForPiece(piece, (r, c), self.board)
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
            self.board.setPositionWithFen(TEST_FEN)
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self.board.updateWithMove(move)
                    self.board.prettyPrint()
        else:
            print("weird " + words.join())

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
                # try:
                #     self.position(line)
                # except:
                #     print("some error lol")
            elif line.startswith("go"):
                print("GOING")
            elif line.startswith("print"):
                self.board.prettyPrint()
                print(self.board.legalMoves())
            elif line.startswith("end"):
                print("goodbye")
                break

engine = Engine()
engine.run()
