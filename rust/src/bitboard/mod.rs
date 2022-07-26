/*
Bitboard is an implementation of a chess board using bit strings.
The Board itself is represented using an array of 8 unsigned 32-bit ints.
Each piece is 4 bits: 1 bit for the side it belongs to, and 3 bits for the
piece type.
*/
// extern crate num;
// #[macro_use]
// extern crate num_derive;

// Constants and Enums
#![allow(dead_code)]
const BOARD_SIZE: u32 = 8;
const PIECE_SIZE: u32 = 4;
const PIECE_MASK: u32 = 0b1111;

const ROW_OFFSET: u8 = 3;
const ROW_MASK: u8 = 0b111000;
const COL_MASK: u8 = 0b000111;
// const INDEX_MASK: u8 = 0b111111;

const PIECE_TYPE_MASK: u32 = 0b0111;
const PIECE_SIDE_MASK: u32 = 0b1000;
const PIECE_SIDE: u32 = 3;

const META_SIDE_TO_MOVE: u16 = 0;
const META_SIDE_TO_MOVE_MASK: u16 = 0b1;
const META_CASTLE: u16 = 1;
const META_CASTLE_MASK: u16 = 0b1111;
const META_ENPASSANT: u16 = 5;
const META_ENPASSANT_MASK: u16 = 0b111111;

macro_rules! piece_type {
    ($bits:ident) => {
        $bits & PIECE_TYPE_MASK
    };
}

// Fenstrings
pub const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
pub const TRICKY_FEN: &str = "r3k2r/pPppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";

#[derive(FromPrimitive)]
enum Pieces {
    Empty = 0,
    Pawn = 1,
    Knight = 2,
    Bishop = 3,
    Rook = 4,
    Queen = 5,
    King = 6,
}

// Struct definitions
#[derive(Copy, Clone)]
pub struct ArrayBoard {
    // Represents the board state--each 8-bit entry is a piece. We only need 4 bits to represent
    // each piece, so this represntation does double the amount of space required.
    board: [u8; 64],
    // Represents the meta data:
    //   - meta[0] = side to move
    //   - meta[1:4] = castles
    //   - meta[4:10] = en passant index
    meta: u16,
}

#[allow(dead_code)]
pub struct BitMove {
    source_square: u8,
    dest_square: u8,
    promote_to: u8,
    meta: u8,
}

// Private Helper functions
fn char_to_piece(piece: char) -> u32 {
    match piece.to_ascii_lowercase() {
        'p' => Pieces::Pawn as u32,
        'n' => Pieces::Knight as u32,
        'b' => Pieces::Bishop as u32,
        'r' => Pieces::Rook as u32,
        'q' => Pieces::Queen as u32,
        'k' => Pieces::King as u32,
        _ => Pieces::Empty as u32,
    }
}

fn piece_to_char(piece: u32) -> char {
    match num::FromPrimitive::from_u32(piece) {
        Some(Pieces::Pawn) => 'p',
        Some(Pieces::Knight) => 'n',
        Some(Pieces::Bishop) => 'b',
        Some(Pieces::Rook) => 'r',
        Some(Pieces::Queen) => 'q',
        Some(Pieces::King) => 'k',
        _ => ' ',
    }
}

fn algebraic_to_index(alg: &str) -> u16 {
    let col = (alg.bytes().nth(0).unwrap() - ('a' as u8)) as u16;
    let row = alg.chars().nth(1).unwrap().to_digit(10).unwrap() as u16;
    (BOARD_SIZE as u16) * (8 - row) + col
}

fn index_to_algebraic(index: u32) -> String {
    let file = (('a' as u8) + (index % BOARD_SIZE) as u8) as char;
    let rank = 8 - (index / BOARD_SIZE);
    String::from(file) + &rank.to_string()
}

// Struct implementations
impl ArrayBoard {
    // Static factory method
    pub fn create_from_fen(fen: &str) -> ArrayBoard {
        let fen_arr: Vec<&str> = fen.split(' ').collect();
        let mut board: [u8; 64] = [0; 64];
        let mut index: usize = 0;
        for (i, fen_row) in fen_arr[0].split('/').enumerate() {
            for c in fen_row.chars() {
                if c.is_digit(10) {
                    index += c.to_digit(10).unwrap() as usize;
                    continue;
                }
                let player = if c.is_lowercase() { 0 } else { 1 };
                board[index] = ((player << PIECE_SIDE) | char_to_piece(c)) as u8;
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

    // Make move logic.
    fn get_piece(&self, index: usize) -> u32 {
        self.board[index] as u32
    }

    fn white_to_move(&self) -> bool {
        (self.meta & 1) == 1
    }

    fn side_to_move(&self) -> u32 {
        ((self.meta & 1) << PIECE_SIDE) as u32
    }

    fn remove_piece(&mut self, index: usize) {
        self.board[index] = 0;
    }

    fn add_piece(&mut self, index: usize, piece: u8) {
        self.board[index] = piece;
    }

    fn get_enpassant(&self) -> u8 {
        ((self.meta & (META_ENPASSANT_MASK << META_ENPASSANT)) >> META_ENPASSANT) as u8
    }

    fn is_opponent_piece(&self, piece: u32) -> bool {
        (self.meta & META_SIDE_TO_MOVE_MASK == 0) != (PIECE_SIDE_MASK & piece == 0)
    }

    pub fn make_move(&self, bit_move: BitMove) -> ArrayBoard {
        let mut new_board = self.clone();
        let source_row = (bit_move.source_square & ROW_MASK) >> ROW_OFFSET;
        let source_col = bit_move.source_square & COL_MASK;
        let dest_row = (bit_move.dest_square & ROW_MASK) >> ROW_OFFSET;
        let dest_col = bit_move.dest_square & COL_MASK;
        let promote_to = bit_move.promote_to;

        let source_piece = self.get_piece(bit_move.source_square as usize);
        let dest_piece = self.get_piece(bit_move.dest_square as usize);
        let mut end_piece = source_piece;

        if (source_piece == 0) || self.is_opponent_piece(source_piece) {
            self.pretty_print(true);
            panic!("Illegal move: {}", bit_move.to_string());
        }

        new_board.meta &= !(META_ENPASSANT_MASK << META_ENPASSANT);
        if piece_type!(source_piece) == (Pieces::Pawn as u32) {
            // Pawn promotion
            if dest_row == 0 || dest_row == 7 {
                if bit_move.promote_to == 0 {
                    end_piece = self.side_to_move() | Pieces::Queen as u32;
                } else {
                    end_piece = self.side_to_move() | bit_move.promote_to as u32;
                }
            // En passant logic
            } else if bit_move.dest_square == self.get_enpassant() {
                // Captured piece is on same row as source, same col as dest.
                let captured =
                    (bit_move.source_square & ROW_MASK) | bit_move.dest_square & COL_MASK;
                new_board.remove_piece(captured as usize);
            }
            // Double advance
            if bit_move.source_square.abs_diff(bit_move.dest_square) == 0o20 {
                let ep_row = if self.white_to_move() { 0o50 } else { 0o20 } as u16;
                let source_col = (bit_move.source_square & COL_MASK) as u16;
                new_board.meta |= ((ep_row | source_col) << META_ENPASSANT) as u16;
            }
        }

        new_board.meta ^= 1;
        new_board.remove_piece(bit_move.source_square as usize);
        new_board.add_piece(bit_move.dest_square as usize, end_piece as u8);
        new_board
    }

    // DEBUGGING AND PRINTING FUNCTIONS ===================================
    pub fn pretty_print(&self, verbose: bool) {
        if verbose {
            println!(" ---------------- BOARD STATE ----------------- ");
            // println!("  Board bits as hexa: (pieces are flipped left to right)");
            // for (i, piece) in self.board.enumerate() {
            //     println!("    {:08x}", i);
            // }
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

            // let mut row_str = String::from("");
            let piece_bits = self.board[i as usize] as u32;
            let piece = piece_to_char(piece_type!(piece_bits));
            let side = piece_bits & 0b1000;
            if side == 0 {
                print!("{}", piece);
                // row_str.push(piece);
                // row_str.push(' ');
            } else {
                print!("{}", piece.to_ascii_uppercase());
                // row_str.push(piece.to_ascii_uppercase());
                // row_str.push(' ');
            }
            if i % BOARD_SIZE == 7 {
                println!("|");
            }
        }
    }
}

impl BitMove {
    pub fn from_move(mv: &str) -> BitMove {
        let source_square = algebraic_to_index(&mv[..2]) as u8;
        let dest_square = algebraic_to_index(&mv[2..4]) as u8;
        let promote_to = match mv.chars().nth(4) {
            Some('q') => Pieces::Queen as u8,
            Some('r') => Pieces::Rook as u8,
            Some('b') => Pieces::Bishop as u8,
            Some('n') => Pieces::Knight as u8,
            _ => 0,
        };
        BitMove {
            source_square,
            dest_square,
            promote_to,
            meta: 0,
        }
    }

    pub fn to_string(&self) -> String {
        let mut move_str = index_to_algebraic(self.source_square as u32)
            + &index_to_algebraic(self.dest_square as u32);
        move_str.push(piece_to_char(self.promote_to as u32));
        move_str
    }
}
