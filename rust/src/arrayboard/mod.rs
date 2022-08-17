/*
Bitboard is an implementation of a chess board using bit strings.
The Board itself is represented using an array of 8 unsigned 32-bit ints.
Each piece is 4 bits: 1 bit for the side it belongs to, and 3 bits for the
piece type.
*/
#![allow(dead_code)]
pub mod generate_moves;

// Constants and Enums
const BOARD_SIZE: u32 = 8;
const PIECE_SIZE: u32 = 4;
const PIECE_MASK: u32 = 0b1111;

const ROW_OFFSET: u8 = 3;
const ROW_MASK: u8 = 0b111000;
const COL_MASK: u8 = 0b000111;
// const INDEX_MASK: u8 = 0b111111;

const PIECE_TYPE_MASK: u32 = 0b1110;
const PIECE_SIDE_MASK: u32 = 0b0001;
const PIECE_TYPE: u32 = 1;

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

#[derive(FromPrimitive, Copy, Clone)]
pub enum PieceType {
    Empty = 0,
    Pawn = 1,
    Knight = 2,
    Bishop = 3,
    Rook = 4,
    Queen = 5,
    King = 6,
}

pub fn piece_type(piece: u32) -> u32 {
    (piece & PIECE_TYPE_MASK) >> PIECE_TYPE
}

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

#[allow(dead_code)]
#[derive(Copy, Clone)]
pub struct BitMove {
    source_square: u8,
    dest_square: u8,
    promote_to: Option<PieceType>,
    pub meta: u16,
}

// Private Helper functions
fn char_to_piece(piece: char) -> u32 {
    match piece.to_ascii_lowercase() {
        'p' => PieceType::Pawn as u32,
        'n' => PieceType::Knight as u32,
        'b' => PieceType::Bishop as u32,
        'r' => PieceType::Rook as u32,
        'q' => PieceType::Queen as u32,
        'k' => PieceType::King as u32,
        _ => PieceType::Empty as u32,
    }
}

fn piece_to_char(piece: u32, if_none: &str) -> &str {
    match num::FromPrimitive::from_u32(piece) {
        Some(PieceType::Pawn) => "p",
        Some(PieceType::Knight) => "n",
        Some(PieceType::Bishop) => "b",
        Some(PieceType::Rook) => "r",
        Some(PieceType::Queen) => "q",
        Some(PieceType::King) => "k",
        _ => if_none,
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

pub fn is_piece_white(piece: u32) -> bool {
    (PIECE_SIDE_MASK & piece) == 1
}

fn piece_to_bits(piece: PieceType, side: u8) -> u8 {
    ((piece as u8) << (PIECE_TYPE as u8)) | side
}

// Struct implementations
impl ArrayBoard {
    // Static factory method
    pub fn create_from_fen(fen: &str) -> ArrayBoard {
        let fen_arr: Vec<&str> = fen.split(' ').collect();
        let mut board: [u8; 64] = [0; 64];
        let mut index: usize = 0;
        for fen_row in fen_arr[0].split('/') {
            for c in fen_row.chars() {
                if c.is_digit(10) {
                    index += c.to_digit(10).unwrap() as usize;
                    continue;
                }
                let player = if c.is_lowercase() { 0 } else { 1 };
                board[index] = (player | (char_to_piece(c) << PIECE_TYPE)) as u8;
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

    // Getters ======================================================
    pub fn white_to_move(&self) -> bool {
        (self.meta & PIECE_SIDE_MASK as u16) == 1
    }

    fn side_to_move(&self) -> u8 {
        (self.meta & PIECE_SIDE_MASK as u16) as u8
    }

    fn get_enpassant(&self) -> u8 {
        ((self.meta & (META_ENPASSANT_MASK << META_ENPASSANT)) >> META_ENPASSANT) as u8
    }

    fn is_opponent_piece(&self, piece: u32) -> bool {
        (self.meta & META_SIDE_TO_MOVE_MASK == 0) != (PIECE_SIDE_MASK & piece == 0)
    }

    pub fn is_king_checked(&self) -> bool {
        (self.meta & META_KING_CHECK_MASK) > 0
    }

    // MAKE MOVE logic ==============================================
    pub fn get_piece(&self, index: usize) -> u32 {
        self.board[index] as u32
    }

    fn remove_piece(&mut self, index: usize) {
        self.board[index] = 0;
    }

    fn add_piece(&mut self, index: usize, piece: u8) {
        self.board[index] = piece;
    }

    fn castle_logic(&mut self, bm: &BitMove, piece: u32) {
        if piece_type(piece) == (PieceType::King as u32) {
            let rook = piece_to_bits(PieceType::Rook, self.side_to_move());
            match (bm.source_square, bm.dest_square) {
                (0o04, 0o02) => {
                    self.remove_piece(0o00);
                    self.add_piece(0o03, rook);
                }
                (0o04, 0o06) => {
                    self.remove_piece(0o07);
                    self.add_piece(0o05, rook);
                }
                (0o74, 0o72) => {
                    self.remove_piece(0o70);
                    self.add_piece(0o73, rook);
                }
                (0o74, 0o76) => {
                    self.remove_piece(0o77);
                    self.add_piece(0o75, rook);
                }
                _ => (),
            }
            // META_CASTLE = 1;
            if self.white_to_move() {
                self.meta &= !(0b11000);
            } else {
                self.meta &= !(0b00110);
            }
        }

        // Remove castle possibility when the rook moves
        if piece_type(piece) == (PieceType::Rook as u32) {
            // META_CASTLE = 1;
            self.meta &= match (self.white_to_move(), (bm.source_square & 0b111) == 7) {
                (false, true) => !(0b00010),
                (false, false) => !(0b00100),
                (true, true) => !(0b01000),
                (true, false) => !(0b10000),
            };
        }
        self.meta &= match (bm.dest_square, self.white_to_move()) {
            (0o00, true) => !(0b00100),  // white takes black queen's rook
            (0o07, true) => !(0b00010),  // white takes black king's rook
            (0o70, false) => !(0b10000), // black takes white queen's rook
            (0o77, false) => !(0b01000), // black takes white king's rook
            _ => !(0),
        }
    }

    pub fn make_move(&self, bit_move: &BitMove) -> ArrayBoard {
        let mut new_board = self.clone();

        let source_piece = self.get_piece(bit_move.source_square as usize);
        let mut end_piece = source_piece as u8;

        if (source_piece == 0) || self.is_opponent_piece(source_piece) {
            self.pretty_print(true);
            panic!("Illegal move: {}", bit_move.to_string());
        }

        new_board.castle_logic(&bit_move, source_piece);

        new_board.meta &= !(META_ENPASSANT_MASK << META_ENPASSANT);
        if piece_type(source_piece) == (PieceType::Pawn as u32) {
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
                new_board.remove_piece(captured as usize);
            }
            // Double advance
            if bit_move.source_square.abs_diff(bit_move.dest_square) == 0o20 {
                let ep_row = if self.white_to_move() { 0o50 } else { 0o20 } as u16;
                let source_col = (bit_move.source_square & COL_MASK) as u16;
                new_board.meta |= ((ep_row | source_col) << META_ENPASSANT) as u16;
            }
        }
        if bit_move.meta & generate_moves::MOVE_CHECK > 0 {
            new_board.meta |= META_KING_CHECK_MASK;
        } else {
            new_board.meta &= !META_KING_CHECK_MASK;
        }

        new_board.meta ^= META_SIDE_TO_MOVE_MASK;
        new_board.remove_piece(bit_move.source_square as usize);
        new_board.add_piece(bit_move.dest_square as usize, end_piece as u8);
        new_board
    }

    // DEBUGGING AND PRINTING FUNCTIONS ===================================
    pub fn pretty_print(&self, verbose: bool) {
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

            // let mut row_str = String::from("");
            let piece_bits = self.board[i as usize] as u32;
            let piece = piece_to_char(piece_type(piece_bits), " ");
            let side = piece_bits & PIECE_SIDE_MASK;
            if side == 0 {
                print!("{}", piece);
            } else {
                print!("{}", piece.to_ascii_uppercase());
            }
            if i % BOARD_SIZE == 7 {
                println!("|");
            }
        }
    }

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

impl BitMove {
    pub fn from_string(mv: &str) -> BitMove {
        let source_square = algebraic_to_index(&mv[..2]) as u8;
        let dest_square = algebraic_to_index(&mv[2..4]) as u8;
        let promote_to = match mv.chars().nth(4) {
            Some('q') => Some(PieceType::Queen),
            Some('r') => Some(PieceType::Rook),
            Some('b') => Some(PieceType::Bishop),
            Some('n') => Some(PieceType::Knight),
            _ => None,
        };
        BitMove {
            source_square,
            dest_square,
            promote_to,
            meta: 0,
        }
    }

    pub fn to_string(&self) -> String {
        index_to_algebraic(self.source_square as u32)
            + &index_to_algebraic(self.dest_square as u32)
            + match self.promote_to {
                Some(PieceType::Queen) => "q",
                Some(PieceType::Knight) => "n",
                Some(PieceType::Bishop) => "b",
                Some(PieceType::Rook) => "r",
                _ => "",
            }
    }

    pub fn create(
        source_square: u8,
        dest_square: u8,
        promote_to: Option<PieceType>,
        meta: u16,
    ) -> BitMove {
        BitMove {
            source_square,
            dest_square,
            promote_to,
            meta,
        }
    }

    pub fn create_capture(
        source_square: u8,
        dest_square: u8,
        attacker: u16,
        victim: u16,
        promote_to: Option<PieceType>,
        meta: u16,
    ) -> BitMove {
        BitMove {
            source_square,
            dest_square,
            promote_to,
            // Most Valuable Victim / Least Valuable Attacker
            meta: meta | (victim * 10 - attacker),
        }
    }
}
