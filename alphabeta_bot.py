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
TEST_FEN = "rn2k3/2pp1pp1/2b1pn2/1BB5/P3P3/1PN2Q1r/2PP1P1P/R3K1NR w KQq - 0 15"
ALIREZA = "books/lichess_alireza.alg"
DEBUG = False

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
               0,  0,  0, 20, 20,  0,  0,  0, \
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
                -20,-10,-10,-10,-10,-10,-10,-20]
ROOK_VALUES = [0,  0,  0,  0,  0,  0,  0,  0,
              5, 10, 10, 10, 10, 10, 10,  5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
              0,  0,  0,  5,  5,  0,  0,  0]
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
                 20, 30, 10,  0,  0, 10, 30, 20]
KING_ENDGAME = [-50,-40,-30,-20,-20,-30,-40,-50,
                -30,-20,-10,  0,  0,-10,-20,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-30,  0,  0,  0,  0,-30,-30,
                -50,-30,-30,-30,-30,-30,-30,-50]
PAWN_ENDGAME = [0,  0,  0,  0,  0,  0,  0,  0, \
              50, 50, 50, 50, 50, 50, 50, 50, \
              40, 40, 40, 40, 40, 40, 40, 40, \
              30, 30, 30, 30, 30, 30, 30, 30, \
              20, 20, 20, 20, 20, 20, 20, 20, \
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
            if DEBUG:
                self.printBookMoves()
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self._board = self._board.makeMove(move)
                    self._moves += 1
                    if self._bookMoves is None:
                        continue
                    if move in self._bookMoves.getChildren():
                        self._bookMoves = self._bookMoves.getChild(move)
                        if DEBUG:
                            self.printBookMoves()
                    else:
                        self._bookMoves = None
        else:
            print("weird " + words.join())

    def go(self, args):
        bookMove = self.consultBook()
        if bookMove is not None:
            print("bestmove " + bookMove)
            return

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
                if usTime < 300000:
                    self._maxDepth = 4
                elif usTime >= opTime * 1.5:
                    self._maxDepth = 6
                elif usTime >= opTime * 1.2:
                    self._maxDepth = 5

        self._bestMoves = []
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
        info = {}
        info['move'] = ""
        # searcher = Thread(target = self.search, args = (self._board, info,), daemon=True)
        # searcher.start()
        nodes, score = self.search(self._board, info)
        print("bestmove " + info['move'])

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

    def evaluatePosition(board):
        if board.isCheckMate():
            return -100000 if board.whiteToMove() else 100000
        numMinors = 0
        whites, blacks = board.activePieces()
        isEndgame = (len(whites) + len(blacks)) < 14
        evalTable = ENDGAME_TABLE if isEndgame else EVAL_TABLES

        whiteScore = 0
        for piece, index in whites:
            whiteScore += PIECE_VALUES[piece]
            whiteScore += evalTable[piece][index]

        blackScore = 0
        for piece, index in blacks:
            # Eval tables are not symmetric. a8 is at index 0, and specified
            # from white's perspective. Need to correct the index for black.
            # a8 (0)  => a1 (56)
            # a1 (56) => a8 (0)
            # a4 (32) => a5 (24)
            # b8 (1)  => b1 (57)
            # b1 (57) => b1 (1)
            # b4 (33) => b5 (25)
            col = index % 8
            bi = 56 - (index - col) + col
            # print("{}, {} = {}".format(bin(piece), bi, EVAL_TABLES[piece][bi]))
            blackScore += PIECE_VALUES[piece]
            blackScore += evalTable[piece][bi]
        # print("WHITE: {}    BLACK: {}    total: {}".format(whiteScore, blackScore, whiteScore-blackScore))
        # whiteScore = sum([PIECE_VALUES[p] for piece, index in whites])
        # blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def search(self, board, info, moves = "", alpha = -1000000, beta = 1000000, depth = 0):
        if board.isCheckMate():
            return 1, (-100000 if board.whiteToMove() else 100000)
        if len(board.getLegalMoves()) == 0:  # stalemate
            return 1, 0
        if depth == self._maxDepth:
            score = AlphaBetaEngine.evaluatePosition(board)
            return 1, score

        # best move for the active player.
        bestMoves = []
        bestScore = -1000000 if board.whiteToMove() else 1000000
        i = 0
        nodes = 0
        if depth == 0:
            start = time.time()
        legalMoves = board.getLegalMoves()
        for move in legalMoves:
            i += 1
            if depth == 0:
                print("info currmove {} currmovenumber {}".format(move, i), flush=True)
            newBoard = board.makeMove(move)
            path = moves + " " + move
            newNodes, score = self.search(newBoard, {}, path, \
                alpha, beta, depth + 1)
            nodes += newNodes

            if board.whiteToMove() and (score > bestScore):
                bestScore = score
                bestMoves = [move]
                alpha = score
                if DEBUG:
                    print("info depth {} score cp {} nodes {} pv {}".format( \
                        self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                        nodes, path), flush=True)
            elif not board.whiteToMove() and (score < bestScore):
                bestScore = score
                bestMoves = [move]
                beta = score
                if DEBUG:
                    print("info depth {} score cp {} nodes {} pv {}".format( \
                        self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                        nodes, path), flush=True)
            if score == bestScore:
                bestMoves.append(move)
            if alpha > beta:
                if DEBUG:
                    print("{}({}): alpha {} > beta {}: pruning {} other branches".format(\
                        "WHITE" if board.whiteToMove() else "BLACK", \
                        depth, alpha, beta, len(legalMoves) - i))
                break
        if depth == 0:
            info['move'] = random.choice(bestMoves)
            elapsedMs = int((time.time() - start) * 1000)
            print("info depth {} score cp {} time {} nodes {} pv {}".format( \
                self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                elapsedMs, nodes, info['move']), flush=True)
        return nodes, bestScore


if __name__ == "__main__":
    engine = AlphaBetaEngine()
    engine.run()
    # engine.position("position startpos moves e2e4")
    # AlphaBetaEngine.evaluatePosition(engine._board)
