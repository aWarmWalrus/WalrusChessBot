import random
import bitboard
from bitboard import BitBoard
from collections import defaultdict

ENGINE_NAME = "MINIMAX"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "5k2/8/8/R7/2R3K1/8/8/8 w - - 0 1"

PIECE_VALUES = {bitboard.PAWN: 1,
                bitboard.ROOK: 5,
                bitboard.BISHOP: 3,
                bitboard.KNIGHT: 4,
                bitboard.QUEEN: 9,
                bitboard.KING: 100000}

class MiniMaxEngine:
    def __init__(self):
        self._options = defaultdict(str)
        self._board = BitBoard(0)
        self._maxDepth = 1 # in plies

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
            self._board = BitBoard.createFromFen(STARTING_FEN)
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self._board = self._board.makeMove(move)
        else:
            print("weird " + words.join())

    def go(self):
        moves = self._board.getLegalMoves()
        if self._board.isCheckMate():
            print("CHECK MATED SON")
            return
        elif len(moves) == 0:
            print("stale mate...??")
            return
        bestMove, score = self.search(self._board)
        if abs(score) == 100:
            print("Forced check mate found!!")
        print("bestmove " + bestMove)

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
                self._board.prettyPrint()
                print(self._board.getLegalMoves())
            elif line.startswith("end") or line.startswith("quit"):
                print("goodbye")
                break

    """ =============== Minimax implementation ====================="""
    def evaluatePosition(board):
        if board.isCheckMate():
            return -100 if board.whiteToMove() else 100
        whites, blacks = board.activePieces()
        whiteScore = sum([PIECE_VALUES[p] for p in whites])
        blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def search(self, board, depth = 0):
        if board.isCheckMate():
            return "", (-100 if board.whiteToMove() else 100)
        if len(board.getLegalMoves()) == 0:  # stalemate
            return "", 0
        if depth == self._maxDepth:
            score = MiniMaxEngine.evaluatePosition(board)
            return "", score

        # best move for the active player.
        bestMoves = []
        bestScore = -1000 if board.whiteToMove() else 1000
        for move in board.getLegalMoves():
            newBoard = board.makeMove(move)
            _, score = self.search(newBoard, depth + 1)
            if (board.whiteToMove() and (score > bestScore)) or \
                    (not board.whiteToMove() and (score < bestScore)):
                # print("better score: " + str(score))
                # newBoard.prettyPrint()
                bestScore = score
                bestMoves = [move]
                continue
            if score == bestScore:
                # print("same score: " + str(score))
                # newBoard.prettyPrint()
                bestMoves.append(move)
        # print(bestMoves)
        return random.choice(bestMoves), bestScore


if __name__ == "__main__":
    engine = MiniMaxEngine()
    # engine._board = BitBoard.createFromFen(TEST_FEN)
    # print(engine.go())
    engine.run()
