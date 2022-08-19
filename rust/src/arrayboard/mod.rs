/*
Bitboard is an implementation of a chess board using bit strings.
The Board itself is represented using an array of 8 unsigned 32-bit ints.
Each piece is 4 bits: 1 bit for the side it belongs to, and 3 bits for the
piece type.
*/
#![allow(dead_code)]
pub mod generate_moves;

use crate::chessboard::ChessBoard;
use crate::moves::BitMove;
use crate::piece::{
    char_to_piece, is_piece_white, piece_to_bits, piece_to_char, piece_type, PieceType,
};

// Constants and Enums
const BOARD_SIZE: u32 = 8;
const PIECE_SIZE: u32 = 4;
const PIECE_MASK: u32 = 0b1111;

const ROW_OFFSET: u8 = 3;
const ROW_MASK: u8 = 0b111000;
const COL_MASK: u8 = 0b000111;
// const INDEX_MASK: u8 = 0b111111;

//   - meta[0] = side to move
//   - meta[1:5] = castles
//   - meta[5:11] = en passant index
//   - meta[11] = a king is checked
const META_SIDE_TO_MOVE: u16 = 0;
const META_SIDE_TO_MOVE_MASK: u16 = 0b1;
const META_CASTLE: u16 = 1;
const META_CASTLE_MASK: u16 = 0b1111;
const META_ENPASSANT: u16 = 5;
const META_ENPASSANT_MASK: u16 = 0b111111;
const META_KING_CHECK_MASK: u16 = 0b100000000000;
const META_KING_CHECK: u16 = 10;

// Fenstrings
pub const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
pub const PERFT2_FEN: &str = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -";
pub const TEST_FEN: &str = "r3k2r/6B1/8/8/8/8/1b4b1/R3K2R b KQk - 0 1";
pub const TRICKY_FEN: &str = "r3k2r/pPppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
// pub const CASTLE_FEN: &str = "r3k2r/pppp1ppp/3b1n2/1nb1pq2/4P3/1QNBBN2/PPPP1PPP/R3K2R w KQkq - 0 1";

// Struct definitions
#[derive(Copy, Clone, Eq, Hash)]
pub struct ArrayBoard {
    // Represents the board state--each 8-bit entry is a piece. We only need 4 bits to represent
    // each piece, so this represntation does double the amount of space required.
    board: [u8; 64],
    // Represents the meta data:
    //   - meta[0] = side to move
    //   - meta[1:5] = castles
    //   - meta[5:11] = en passant index
    //   - meta[11] = a king is checked
    meta: u16,
}

impl PartialEq for ArrayBoard {
    fn eq(&self, other: &ArrayBoard) -> bool {
        other.board == self.board && other.meta == self.meta
    }
}

// Private Helper functions
pub fn algebraic_to_index(alg: &str) -> u16 {
    let col = (alg.bytes().nth(0).unwrap() - ('a' as u8)) as u16;
    let row = alg.chars().nth(1).unwrap().to_digit(10).unwrap() as u16;
    (BOARD_SIZE as u16) * (8 - row) + col
}

pub fn index_to_algebraic(index: u32) -> String {
    let file = (('a' as u8) + (index % BOARD_SIZE) as u8) as char;
    let rank = 8 - (index / BOARD_SIZE);
    String::from(file) + &rank.to_string()
}

// Struct implementations
impl ArrayBoard {
    // Getters ======================================================
    fn side_to_move(&self) -> u8 {
        (self.meta & META_SIDE_TO_MOVE_MASK) as u8
    }

    fn not_side_to_move(&self) -> u8 {
        ((self.meta & META_SIDE_TO_MOVE_MASK) ^ META_SIDE_TO_MOVE_MASK) as u8
    }

    fn get_enpassant(&self) -> u8 {
        ((self.meta & (META_ENPASSANT_MASK << META_ENPASSANT)) >> META_ENPASSANT) as u8
    }

    fn is_opponent_piece(&self, piece: u32) -> bool {
        (self.meta & META_SIDE_TO_MOVE_MASK == 0) == is_piece_white(piece)
    }

    // MAKE MOVE logic ==============================================
    fn remove_piece(&mut self, index: usize) {
        self.board[index] = 0;
    }

    fn add_piece(&mut self, index: usize, piece: u8) {
        self.board[index] = piece;
    }

    fn find_piece(&self, piece: u8) -> Option<u32> {
        for i in 0..64 {
            if self.board[i] == piece {
                return Some(i as u32);
            }
        }
        println!(
            "Piece not found on board {} {:#?} ({:0b})",
            if is_piece_white(piece as u32) {
                "White"
            } else {
                "Black"
            },
            piece_type(piece as u32),
            piece
        );
        return None;
    }

    fn rook_castle_destinations(bm: &BitMove) -> (usize, usize) {
        match (bm.source_square, bm.dest_square) {
            (0o04, 0o02) => (0o00, 0o03),
            (0o04, 0o06) => (0o07, 0o05),
            (0o74, 0o72) => (0o70, 0o73),
            (0o74, 0o76) => (0o77, 0o75),
            _ => (0o00, 0o00),
        }
    }

    fn make_castle_logic(&mut self, bm: &BitMove, piece: u32) {
        if piece_type(piece) == PieceType::King {
            let rook = piece_to_bits(PieceType::Rook, self.side_to_move());
            let (rook_src, rook_dest) = Self::rook_castle_destinations(bm);
            if rook_src != 0 {
                self.remove_piece(rook_src);
                self.add_piece(rook_dest, rook);
            }
            // META_CASTLE = 1;
            if self.white_to_move() {
                self.meta &= !(0b11000);
            } else {
                self.meta &= !(0b00110);
            }
        }

        // Remove castle possibility when the rook moves
        if piece_type(piece) == PieceType::Rook {
            // META_CASTLE = 1;
            self.meta &= match (self.white_to_move(), (bm.source_square & 0b111) == 7) {
                (false, true) => !(0b00010),
                (false, false) => !(0b00100),
                (true, true) => !(0b01000),
                (true, false) => !(0b10000),
            };
        }
        self.meta &= match (bm.dest_square, self.white_to_move()) {
            (0o07, true) => !(0b00010),  // white takes black king's rook
            (0o00, true) => !(0b00100),  // white takes black queen's rook
            (0o77, false) => !(0b01000), // black takes white king's rook
            (0o70, false) => !(0b10000), // black takes white queen's rook
            _ => !(0),
        };
    }

    fn is_king_safe(&self) -> Option<bool> {
        let our_king = piece_to_bits(PieceType::King, self.side_to_move());
        match self.find_piece(our_king) {
            Some(i) => Some(!self.is_square_attacked(i, !self.white_to_move())),
            None => None,
        }
    }

    // DEBUGGING AND PRINTING FUNCTIONS ===================================
    pub fn print_legal_moves(&self, verbose: bool) {
        print!("Legal moves: ");
        if verbose {
            println!();
        }
        for m in self.generate_moves() {
            if verbose {
                println!("{} ({:b})", m.to_string(), m.meta);
                continue;
            }
            print!("{}, ", m.to_string());
        }
        println!("");
    }
}

impl ChessBoard for ArrayBoard {
    fn get_piece(&self, index: usize) -> u32 {
        self.board[index] as u32
    }

    fn white_to_move(&self) -> bool {
        (self.meta & META_SIDE_TO_MOVE_MASK as u16) == 1
    }

    fn is_king_checked(&self) -> bool {
        !self.is_king_safe().unwrap()
        // (self.meta & META_KING_CHECK_MASK) > 0
    }

    fn hash(&self) -> u64 {
        0
    }

    // Static factory method
    fn create_from_fen(fen: &str) -> ArrayBoard {
        let fen_arr: Vec<&str> = fen.split(' ').collect();
        let mut board: [u8; 64] = [0; 64];
        let mut index: usize = 0;
        for fen_row in fen_arr[0].split('/') {
            for c in fen_row.chars() {
                if c.is_digit(10) {
                    index += c.to_digit(10).unwrap() as usize;
                    continue;
                }
                board[index] = char_to_piece(c);
                index += 1;
            }
        }
        // META: Side to play
        let mut meta = 0;
        if fen_arr[1].starts_with('w') {
            meta |= 1
        }
        // META: Castles
        for c in fen_arr[2].chars() {
            // HACK ALERT: Start one bit over since sideToMove bit is bit 0
            let ind = match c {
                'k' => 0b00010,
                'q' => 0b00100,
                'K' => 0b01000,
                'Q' => 0b10000,
                _ => 0,
            };
            meta |= ind;
        }
        // META: En Passant
        if !fen_arr[3].eq_ignore_ascii_case("-") {
            meta |= algebraic_to_index(fen_arr[3]) << 4;
        }
        ArrayBoard { board, meta }
    }

    fn make_move(&mut self, bit_move: &mut BitMove) -> Option<bool> {
        // First, save the board's current meta in bit_move for call to take_back_move() later.
        bit_move.board_meta = self.meta;

        let source_piece = self.get_piece(bit_move.source_square as usize);
        let mut end_piece = source_piece as u8;

        if (source_piece == 0) || self.is_opponent_piece(source_piece) {
            self.pretty_print(true);
            panic!("Illegal move: {}", bit_move.to_string());
        }

        self.make_castle_logic(&bit_move, source_piece);

        let mut new_meta = self.meta & !(META_ENPASSANT_MASK << META_ENPASSANT);
        if piece_type(source_piece) == PieceType::Pawn {
            let dest_row = (bit_move.dest_square & ROW_MASK) >> ROW_OFFSET;
            // Pawn promotion
            if dest_row == 0 || dest_row == 7 {
                end_piece = match bit_move.promote_to {
                    Some(p) => piece_to_bits(p, self.side_to_move()),
                    None => piece_to_bits(PieceType::Queen, self.side_to_move()),
                }
            // En passant logic
            } else if bit_move.dest_square == self.get_enpassant() {
                // Captured piece is on same row as source, same col as dest.
                let captured =
                    (bit_move.source_square & ROW_MASK) | bit_move.dest_square & COL_MASK;
                self.remove_piece(captured as usize);
            }
            // Double advance
            if bit_move.source_square.abs_diff(bit_move.dest_square) == 0o20 {
                let ep_row = if self.white_to_move() { 0o50 } else { 0o20 } as u16;
                let source_col = (bit_move.source_square & COL_MASK) as u16;
                new_meta |= ((ep_row | source_col) << META_ENPASSANT) as u16;
            }
        }
        self.meta = new_meta;
        if bit_move.is_check() {
            self.meta |= META_KING_CHECK_MASK;
        } else {
            self.meta &= !META_KING_CHECK_MASK;
        }

        self.remove_piece(bit_move.source_square as usize);
        self.add_piece(bit_move.dest_square as usize, end_piece as u8);

        match self.is_king_safe() {
            Some(b) => {
                self.meta ^= META_SIDE_TO_MOVE_MASK;
                return Some(b);
            }
            None => {
                println!("Illegal move!");
                self.pretty_print(true);
                None
            }
        }
    }

    fn take_back_move(&mut self, mv: &BitMove) {
        // Restoring the board meta needs to happen before calls to self.side_to_move() and self.get_enpassant().
        self.meta = mv.board_meta;

        // Undo castle moves.
        if mv.source_piece == PieceType::King {
            let (rook_src, rook_dest) = Self::rook_castle_destinations(mv);
            if rook_src != 0 {
                let rook = piece_to_bits(PieceType::Rook, self.side_to_move());
                self.remove_piece(rook_dest);
                self.add_piece(rook_src, rook);
            }
        }

        self.add_piece(
            mv.source_square as usize,
            piece_to_bits(mv.source_piece, self.side_to_move()),
        );

        // Decide if we need to restore any captured pieces.
        if mv.captured == PieceType::Empty {
            self.remove_piece(mv.dest_square as usize);

        // Special en-passant case.
        } else if mv.source_piece == PieceType::Pawn
            && mv.dest_square == self.get_enpassant()
            && mv.dest_square > 0
        {
            // mv.captured should == Pawn
            let ep_index = (mv.source_square & ROW_MASK) | (mv.dest_square & COL_MASK);
            self.add_piece(
                ep_index as usize,
                piece_to_bits(PieceType::Pawn, self.not_side_to_move()),
            );
            self.remove_piece(mv.dest_square as usize);
        } else {
            self.add_piece(
                mv.dest_square as usize,
                piece_to_bits(mv.captured, self.not_side_to_move()),
            );
        }
    }

    fn generate_moves(&self) -> Vec<BitMove> {
        let mut moves: Vec<BitMove> = Vec::new();
        for i in 0..64 {
            let piece = self.get_piece(i);
            if piece == 0 || self.is_opponent_piece(piece) {
                continue;
            }
            moves.append(&mut self.legal_moves_for_piece(piece_type(piece), i as u8));
        }
        moves.append(&mut self.legal_castle_moves());
        // moves = self.filter_king_checks(moves);
        // Reverse sort--higher meta is prioritized.
        moves.sort_unstable_by(|&mv1, &mv2| mv2.meta.cmp(&mv1.meta));
        moves
    }

    fn pretty_print(&self, verbose: bool) {
        if verbose {
            println!(" ---------------- BOARD STATE ----------------- ");
            println!("  Board metadata in binary:");
            let enpassant = (self.meta & (META_ENPASSANT_MASK << META_ENPASSANT)) >> META_ENPASSANT;
            let castles = (self.meta & (META_CASTLE_MASK << META_CASTLE)) >> META_CASTLE;
            let side_to_move = self.meta & 1;
            println!(
                "     {:06b} |  {:04b}  | {}",
                enpassant, castles, side_to_move
            );
            println!(" en passant | castle | side to move");
        }
        for i in 0..64 {
            if i % BOARD_SIZE == 0 {
                print!("|");
            } else {
                print!(" ");
            }

            let piece_bits = self.board[i as usize] as u32;
            print!("{}", piece_to_char(piece_bits, " "));
            if i % BOARD_SIZE == 7 {
                println!("|");
            }
        }
    }
}
