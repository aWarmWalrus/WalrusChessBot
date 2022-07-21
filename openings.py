from bitboard import BitBoard, PAWN, BISHOP, ROOK, KING, QUEEN, KNIGHT
from collections import defaultdict
import sys

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
PIECE_MAP = {"P": PAWN, \
            "N": KNIGHT, \
            "R": ROOK, \
            "B": BISHOP, \
            "Q": QUEEN, \
            "K": KING}

def convertPgnToAlgebraic(line):
    newFile = open("lichess_alireza.pgn", "a")
    board = BitBoard.createFromFen(STARTING_FEN)
    algebraic = []
    for omove in line.split():
        move = omove
        if move[-1] == "." or move[0].isdigit():
            continue
        move = move.strip("+#")
        move = move.replace('x', '')
        # print("|{}|".format(move))
        # board.prettyPrint()
        if move == "O-O":
            alg = "e1g1" if board.whiteToMove() else "e8g8"
            algebraic.append(alg)
            board = board.makeMove(alg)
            continue
        if move == "O-O-O":
            alg = "e1c1" if board.whiteToMove() else "e8c8"
            algebraic.append(alg)
            board = board.makeMove(alg)
            # raise Exception("HAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa")
            continue
        if "=" in move:
            dest, promo = move.split("=")
            # print("ASDFASDF " + dest + promo.lower())
            try:
                legalMoves = board.getLegalMoves()
            except Exception as e:
                print(line)
                raise e
            for move in legalMoves:
                if (dest[-2:] in move) and (promo.lower() in move):
                    board = board.makeMove(move)
                    algebraic.append(move)
                    # print("Found a move " + move)
                    break
            continue
        dest = move[-2:]
        piece = "P" if move[0].islower() else move[0]
        if move[0].isupper():
            move = move[1:]
        bitPiece = PIECE_MAP[piece]
        # print("\nmove: {}  piece: {}  dest: {}  {}".format(move, bin(bitPiece), dest, \
        #     "WHITE" if board.whiteToMove() else "BLACK"))
        try:
            legalMoves = board.getLegalMoves()
        except Exception as e:
            print(line)
            raise e
        possibles = []
        for lm in legalMoves:
            src = BitBoard.pieceAtAlgebraic(board._bits, lm[0:2])
            if lm[-2:] == dest and bitPiece == BitBoard.pieceType(src):
                possibles.append(lm)
        if len(possibles) == 1:
            lm = possibles[0]
            src = BitBoard.pieceAtAlgebraic(board._bits, lm[0:2])
            board = board.makeMove(possibles[0])
            algebraic.append(possibles[0])
            if bitPiece != BitBoard.pieceType(src):
                # print("hmmm... SAN: {}   board: {}   {}".format(piece, bin(src), lm[0:2]))
                raise Exception("hmm")
            continue
        if len(possibles) > 1:
            clarifier = move[0]
            # print("Too many possibilities.... " + clarifier)
            # print(possibles)
            for p in possibles:
                if clarifier in p[0:2]:
                    # print("{} {}".format(p, clarifier))
                    board = board.makeMove(p)
                    algebraic.append(p)
                    break
            # raise Exception("POOPOO {}:  legals {}  white to play? {}".format(\
            #     move, list(filter((lambda lm : lm[-2:0] == dest), legalMoves)), board.whiteToMove()))
            continue

        print(line)
        print("|{}|".format(omove))
        print("Not enough possibilities")
        print("algebraic so far: ", algebraic)
        board.prettyPrint()
        # TODO: Handle pawn promotion...
        raise Exception("POOPOO {}:  legals {}  white to play? {}".format(\
            move, list(filter((lambda lm : lm[-2:0] == dest), legalMoves)), board.whiteToMove()))
    return algebraic

class OpeningTree:
    def generateFromFile(file):
        f = open(file)
        openingBook = OpeningTree(None, "")
        for l in f:
            if not l.startswith("1"):
                continue
            moves = convertPgnToAlgebraic(l)
            # print(moves)
            child = openingBook
            for move in moves:
                # if move[0].isdigit():
                #     continue
                child = child.getChild(move)
        return openingBook

    def __init__(self, parent, move):
        self._move = move
        self._parent = parent
        self._counter = 1
        self._children = {}

    def increment(self):
        self._counter += 1

    def getMove(self):
        return self._move

    def getChild(self, move):
        if move in self._children:
            child = self._children[move]
            child.increment()
            return child
        newChild = OpeningTree(self, move)
        self._children[move] = newChild
        return newChild


if __name__ == "__main__":
    f = open("books/lichess_alireza2003_2022-07-20.pgn")
    newF = open("books/lichess_alireza.pgn", "w")
    for l in f:
        if not l.startswith("1"):
            continue
        moves = convertPgnToAlgebraic(l)
        newF.write(" ".join(moves))
        newF.write("\n")
    # filename = sys.argv[1]
    # tree = OpeningTree.generateFromFile("books/test.pgn")
