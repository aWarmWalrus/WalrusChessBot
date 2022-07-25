import bitboard
import copy
import sys
import random
import time
from bitboard import BitBoard
from collections import defaultdict
from threading import Thread
from openings import OpeningTree

ENGINE_NAME = "ALPHA_BETA"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "8/1b6/p5R1/1p1kp3/3npq2/Q7/PP5P/5rNK w - - 6 38"
ALIREZA = "../../books/lichess_alireza.alg"
DEBUG = True
USE_BOOK = True
QUIESCE = False

POS_INF = 1000000000
NEG_INF = -1000000000
WHITE_MATE = 1000000
BLACK_MATE = -1000000

PIECE_VALUES = {bitboard.PAWN:   100,
                bitboard.KNIGHT: 320,
                bitboard.BISHOP: 330,
                bitboard.ROOK:   500,
                bitboard.QUEEN:  900,
                bitboard.KING:   20000}
PAWN_VALUES = [0,  0,  0,  0,  0,  0,  0,  0, \
              50, 50, 50, 50, 50, 50, 50, 50, \
              10, 10, 20, 30, 30, 20, 10, 10, \
               5,  5, 10, 25, 25, 10,  5,  5, \
               5,  0,  0, 20, 20,  0,  0,  5, \
               5, -5,-10,  0,  0,-10, -5,  5, \
               5, 10, 10,-20,-20, 10, 10,  5, \
               0,  0,  0,  0,  0,  0,  0,  0]
KNIGHT_VALUES = [-50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50]
BISHOP_VALUES = [-20,-10,-10,-10,-10,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0, 10, 10, 10, 10,  0,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  5,  0,  0,  0,  0,  5,-10,
                -20,-10,-30,-10,-10,-30,-10,-20]
ROOK_VALUES = [0,  0,  0,  0,  0,  0,  0,  0,
              5, 10, 10, 10, 10, 10, 10,  5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
              0,  0,  0, 10, 10,  0,  0,  0]
QUEEN_VALUES = [-20,-10,-10, -5, -5,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5,  5,  5,  5,  0,-10,
                 -5,  0,  5,  5,  5,  5,  0, -5,
                  0,  0,  5,  5,  5,  5,  0, -5,
                -10,  5,  5,  5,  5,  5,  0,-10,
                -10,  0,  5,  0,  0,  0,  0,-10,
                -20,-10,-10, -5, -5,-10,-10,-20]
KING_VALUES = [-30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                 20, 20,  0,  0,  0,  0, 20, 20,
                 20, 50, 10,  0,  0, 10, 50, 20]
KING_ENDGAME = [-50,-40,-30,-20,-20,-30,-40,-50,
                -30,-20,-10,  0,  0,-10,-20,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-30,  0,  0,  0,  0,-30,-30,
                -50,-30,-30,-30,-30,-30,-30,-50]
PAWN_ENDGAME = [0,  0,  0,  0,  0,  0,  0,  0, \
             400,400,400,400,400,400,400,400, \
             200,200,200,200,200,200,200,200, \
             100,100,100,100,100,100,100,100, \
              50, 50, 50, 50, 50, 50, 50, 50, \
              10, 10, 10, 10, 10, 10, 10, 10, \
               0,  0,  0,  0,  0,  0,  0,  0, \
               0,  0,  0,  0,  0,  0,  0,  0]
EVAL_TABLES = {bitboard.PAWN:   PAWN_VALUES,
               bitboard.KNIGHT: KNIGHT_VALUES,
               bitboard.BISHOP: BISHOP_VALUES,
               bitboard.ROOK:   ROOK_VALUES,
               bitboard.QUEEN:  QUEEN_VALUES,
               bitboard.KING:   KING_VALUES}
ENDGAME_TABLE = {bitboard.PAWN: PAWN_ENDGAME,
               bitboard.KNIGHT: KNIGHT_VALUES,
               bitboard.BISHOP: BISHOP_VALUES,
               bitboard.ROOK:   ROOK_VALUES,
               bitboard.QUEEN:  QUEEN_VALUES,
               bitboard.KING:   KING_ENDGAME}

class AlphaBetaEngine:
    def __init__(self):
        self._options = defaultdict(str)
        self._board = BitBoard(0)
        self._maxDepth = 5 # in plies
        self._table = {}
        self._moves = 0
        self._nodes = 0
        self._maxQuiesceDepth = 6
        try:
            self._openings = OpeningTree.generateFromFile(ALIREZA)
        except FileNotFoundError:
            self._openings = OpeningTree.generateFromFile("../" + ALIREZA)

    def inputUCI(self):
        print("id name " + ENGINE_NAME)
        print("id author Walrus")
        print("uciok")

    def setOptions(self, line):
        print("unimplemented")

    def isReady(self):
        print("readyok")

    def newGame(self):
        # _bookMoves is a OpeningsTree node that is not None as long as there
        # are still moves remaining.
        self._bookMoves = self._openings
        self._table = {}
        self._moves = 0

    def printBookMoves(self):
        print("book moves (moves #{})".format(self._moves))
        children = self._bookMoves.getChildren()
        for c in children:
            print("  {}: {}".format(c, children[c].getCount()))

    def position(self, line):
        words = line.split()
        assert(words[0] == "position")

        if words[1] == "startpos":
            self._bookMoves = self._openings
            self._moves = 0
            self._board = BitBoard.createFromFen(STARTING_FEN)
            # if DEBUG:
            #     self.printBookMoves()
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self._board = self._board.makeMove(move)
                    self._moves += 1
                    if self._bookMoves is None:
                        continue
                    if move in self._bookMoves.getChildren():
                        self._bookMoves = self._bookMoves.getChild(move)
                        # if DEBUG:
                        #     self.printBookMoves()
                    else:
                        self._bookMoves = None
        elif words[1] == "fen":
            self._bookMoves = None
            self._board = BitBoard.createFromFen(" ".join(words[2:7]))
        else:
            print("weird " + words.join())

    def go(self, args):
        if USE_BOOK:
            bookMove = self.consultBook()
            if bookMove is not None:
                print("bestmove " + bookMove)
                return
        self._nodes = 0

        # Time management
        self._maxDepth = 4
        if len(args) > 1:
            if args[1] == "infinite":
                self._maxDepth = 4
            elif args[1] == "wtime":
                whiteTime = int(args[2])
                blackTime = int(args[4])
                usTime = whiteTime if self._board.whiteToMove() else blackTime
                opTime = blackTime if self._board.whiteToMove() else whiteTime
                if usTime < 900000:
                    self._maxDepth = 4
                # elif usTime >= opTime * 1.5:
                #     self._maxDepth = 5

        moves = self._board.getLegalMoves()
        if len(moves) < 5:
            print("< 5 moves: {}".format(moves))
            self._maxDepth += 1
        print("DEBUG: searching max depth " + str(self._maxDepth))

        if self._board.isCheckMate():
            print("CHECK MATED SON")
            return
        elif len(moves) == 0:
            print("stale mate...??")
            return
        bestPath, score, mateIn = self.search(self._board)
        print("bestmove " + bestPath.split()[0])

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
                self.go(line.split())
            elif line.startswith("print"):
                self._board.prettyPrint()
                print(self._board.getLegalMoves())
                print(AlphaBetaEngine.evaluatePosition(self._board))
            elif line.startswith("end") or line.startswith("quit"):
                print("goodbye")
                break

    """ =============== Alpha Beta implementation ====================="""
    def consultBook(self):
        if self._bookMoves is not None and self._moves < 12:
            children = self._bookMoves.getChildren()
            values = [c.getCount() for c in children.values()]
            return random.choices(list(children.keys()), values)[0]
        return None

    def printDebugInfo(self, bestScore, start, bestMateIn, pv):
        if not DEBUG:
            return
        elapsedMs = int((time.time() - start) * 1000)
        if (bestScore == WHITE_MATE and self._board.whiteToMove()) or \
            (bestScore == BLACK_MATE and not self._board.whiteToMove()):
            scoreInfo = "mate {}".format(int((bestMateIn+1)/2))
        elif abs(bestScore) == WHITE_MATE:
            scoreInfo = "mate {}".format(-1 * int((bestMateIn+1)/2))
        else:
            scoreInfo = "cp {}".format(\
                bestScore * (1 if self._board.whiteToMove() else -1))

        print("info depth {} score {} time {} nodes {} pv {}".format( \
            self._maxDepth, scoreInfo, elapsedMs, self._nodes, pv), flush=True)

    def evaluatePosition(board):
        if board.isCheckMate():
            # We should be checking this in search
            return BLACK_MATE if board.whiteToMove() else WHITE_MATE
        numMinors = 0
        whites, blacks = board.activePieces()
        isEndgame = (len(whites) + len(blacks)) <= 18
        evalTable = ENDGAME_TABLE if isEndgame else EVAL_TABLES

        whiteScore = 0
        for piece, index in whites:
            whiteScore += PIECE_VALUES[piece]
            whiteScore += evalTable[piece][index]

        blackScore = 0
        for piece, index in blacks:
            col = index % 8
            bi = 56 - (index - col) + col
            blackScore += PIECE_VALUES[piece]
            blackScore += evalTable[piece][bi]
        # print("WHITE: {}    BLACK: {}    total: {}".format(whiteScore, blackScore, whiteScore-blackScore))
        # whiteScore = sum([PIECE_VALUES[p] for piece, index in whites])
        # blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def quiesce(self, board, alpha, beta, depth):
        self._nodes += 1
        eval = AlphaBetaEngine.evaluatePosition(board)
        if depth == self._maxQuiesceDepth:
            return eval, POS_INF
        # Stand pat scores
        if board.whiteToMove():
            if eval >= beta:
                return beta, POS_INF
            if eval > alpha:
                alpha = eval
        elif not board.whiteToMove() and eval < alpha:
            if eval <= alpha:
                return alpha, POS_INF
            if eval > beta:
                beta = eval

        bestScore = alpha if board.whiteToMove() else beta
        bestMateIn = POS_INF
        for move in board.getLegalMoves():
            # I think we need to implement piece value ordering.
            # don't quiesce on moves where a more valuable piece takes a less
            # valuable piece.
            if BitBoard.moveCaptureValue(move) < 0:
                continue
            newBoard = board.makeMove(move)
            score, mateIn = self.quiesce(newBoard, alpha, beta, depth+1)
            if board.whiteToMove():
                if score >= beta:
                    return beta, POS_INF
                if score > alpha or (mateIn < bestMateIn and score == WHITE_MATE):
                    bestScore = score
            else:
                if score <= alpha:
                    return alpha, POS_INF
                if score < beta or (mateIn < bestMateIn and score == BLACK_MATE):
                    bestScore = score

            if alpha > beta:
                break

        return bestScore, bestMateIn + 1

    def search(self, board, alpha=NEG_INF, beta=POS_INF, depth=0):
        self._nodes += 1
        if board.isCheckMate():
            return "", (BLACK_MATE if board.whiteToMove() else WHITE_MATE), 1
        if len(board.getLegalMoves()) == 0:  # stalemate
            return "", 0, POS_INF
        if depth >= self._maxDepth:
            # Evaluate using quiescence
            if QUIESCE:
                score, bestMateIn = self.quiesce(board, alpha, beta, depth)
                return "", score, bestMateIn
            else:
                score = AlphaBetaEngine.evaluatePosition(board)
                return "", score, POS_INF
            # print("{}eval: {}".format("  " * depth, score))
            # return "", score, bestMateIn

        bestPath = ""
        # THIS LINE IS A FUNDAMENTAL BUG. it should be:
        # bestScore = alpha if board.whiteToMove() else beta
        # However, it runs much faster this way and I haven't found a scenario
        # where this produces a better result than the "correct" line.
        bestScore = NEG_INF if board.whiteToMove() else POS_INF
        bestMateIn = POS_INF
        if depth == 0:
            start = time.time()
        i = 0
        for move in board.getLegalMoves():
            i += 1
            moveString = BitBoard.moveStr(move)
            if depth == 0:
                print("info currmove {} currmovenumber {}".format(moveString, i), flush=True)

            newBoard = board.makeMove(move)
            path, score, mateIn = self.search(newBoard, alpha, beta, depth + 1)

            if board.whiteToMove() and ((score > alpha) or \
                (mateIn < bestMateIn and score == WHITE_MATE)):
                bestScore = score
                bestPath = moveString + " " + path
                bestMateIn = mateIn
                alpha = score
                if depth == 0:
                    self.printDebugInfo(score, start, mateIn, bestPath)
            elif (not board.whiteToMove()) and ((score < beta) or \
                (mateIn < bestMateIn and score == BLACK_MATE)):
                bestScore = score
                bestPath = moveString + " " + path
                bestMateIn = mateIn
                beta = score
                if depth == 0:
                    self.printDebugInfo(score, start, mateIn, bestPath)
            if alpha > beta:
                # if DEBUG:
                # print("{}{}: alpha {} > beta {}: pruning {} other branches".format(\
                #     "  " * depth, "WHITE" if board.whiteToMove() else "BLACK", \
                #     alpha, beta, len(board.getLegalMoves()) - i))
                break

        if depth == 0:
            self.printDebugInfo(bestScore, \
                start, bestMateIn, bestPath)
        return bestPath, bestScore, bestMateIn + 1


if __name__ == "__main__":
    engine = AlphaBetaEngine()
    engine.run()
    # Scenarios to improve on:
    #  Escapable threats, don't just counter threat:
    #  - r2q1rk1/2p2ppp/p1P1bn2/2b5/3pPN2/1P3P2/PQ1B2PP/RN2K2R b KQ - 6 17
    #  - r2q1r2/2p2p1k/pbP1bn1p/4P3/1P1p3B/3N1P2/P5PP/RNQ1K2R b KQ - 0 23
    #  Trading expensive pieces for cheap pieces (queen for minor??):
    #  -
    # engine.position("position startpos moves g1h3 d7d5 h3g5 h7h6 g5h7 h8h7 h1g1 e7e5 g1h1 g8f6 h1g1 b8c6 g1h1 f8b4 h1g1 c8e6 g1h1 f6e4 h1g1 d8h4 g1h1 b4c5 h1g1 e8d7 g1h1 g7g6 h1g1 b7b6 g1h1")
    # engine._board.prettyPrintVerbose()
    # # engine._board.printLegalMoves()
    # engine.go([])
    # AlphaBetaEngine.evaluatePosition(engine._board)
