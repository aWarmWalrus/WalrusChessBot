from collections import defaultdict

ENGINE_NAME = "ARYA"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

class Array2DBoard:
    def __init__(self):
        self.board = [[" " for _ in range(8)] for _ in range(8)]
        self.whiteToPlay = True

    # TODO: full handle all possible fen strings
    def setPositionWithFen(self, fen):
        fenArr = fen.split(" ")
        self.whiteToPlay = True if fenArr[1] == "w" else False

        rows = fenArr[0].split("/")
        for i in range(len(rows)):
            if rows[i] == "8":
                self.board[i] = [" " for _ in range(8)]
                continue
            for j in range(len(rows[i])):
                self.board[i][j] = rows[i][j]

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


    def legalMovesForPiece(self, piece, coord):
        print(piece)
        print(coord)
        match piece.lower():
            case "p":

                return ["a"]
            case "r":
                return ["a"]
            case "b":
                return ["a"]
            case "n":
                return ["a"]
            case "q":
                return ["a"]
            case "k":
                return ["a"]
        return []


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
            legalMoves += self.legalMovesForPiece(piece, (r, c))
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
