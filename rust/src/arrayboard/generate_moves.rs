// use super::*;
use crate::arrayboard::{ArrayBoard, BOARD_SIZE};
use crate::chessboard::ChessBoard;
use crate::moves::{BitMove, MOVE_CAPTURE, MOVE_CASTLE, MOVE_CHECK, MOVE_PROMO};
use crate::piece::{is_piece_white, piece_to_bits, piece_type, PieceType};

const EMPTY: [(i8, i8); 8] = [
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
];
const ROOK_DIRS: [(i8, i8); 8] = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
];
const BISHOP_DIRS: [(i8, i8); 8] = [
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
];
const ROYAL_DIRS: [(i8, i8); 8] = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
];
const KNIGHT_DIRS: [(i8, i8); 8] = [
    (-1, -2),
    (-2, -1),
    (-2, 1),
    (-1, 2),
    (1, 2),
    (2, 1),
    (2, -1),
    (1, -2),
];
const PIECE_DIRS: [(PieceType, [(i8, i8); 8]); 5] = [
    (PieceType::Knight, KNIGHT_DIRS),
    (PieceType::Bishop, BISHOP_DIRS),
    (PieceType::Rook, ROOK_DIRS),
    (PieceType::Queen, ROYAL_DIRS),
    (PieceType::King, ROYAL_DIRS),
];
const PROMOTIONS: [PieceType; 4] = [
    PieceType::Knight,
    PieceType::Bishop,
    PieceType::Rook,
    PieceType::Queen,
];

// Returns the index and a bool. The returned bool is true iff the computed result
// is out of bounds.
fn index_plus_coord(index: i8, coord: (i8, i8)) -> (usize, bool) {
    let result = index + (coord.0 * 8) + coord.1;
    if result < 0 || result > 63 {
        return (69, true);
    }
    let col = (index % 8) + coord.1;
    (result as usize, (col < 0 || col > 7))
}

fn is_back_rank(index: usize) -> bool {
    index <= 7 || index >= 56
}

impl ArrayBoard {
    fn legal_moves_for_pawn(&self, index: u8) -> Vec<BitMove> {
        let mut moves = Vec::new();
        let forward = if self.white_to_move() { -1 } else { 1 };
        // Pawn takes diagonally
        for d in [(forward, -1), (forward, 1)] {
            let (dest_index, out_of_bounds) = index_plus_coord(index as i8, d);
            if out_of_bounds {
                continue;
            }
            let dest_piece = self.get_piece(dest_index);
            // Pawn takes into a promotion
            if dest_piece != 0 && self.is_opponent_piece(dest_piece) {
                if is_back_rank(dest_index) {
                    for promote_to in PROMOTIONS {
                        moves.push(BitMove::create_capture(
                            index,
                            dest_index as u8,
                            /* source_piece = */ PieceType::Pawn,
                            /* captured = */ piece_type(dest_piece),
                            Some(promote_to),
                            MOVE_PROMO | MOVE_CAPTURE,
                        ));
                    }
                    continue;
                }
                // Pawn takes (non-promotion)
                moves.push(BitMove::create_capture(
                    index,
                    dest_index as u8,
                    /* source_piece = */ PieceType::Pawn,
                    /* captured = */ piece_type(dest_piece),
                    None,
                    MOVE_CAPTURE,
                ));
                continue;
            }
            // En-passant pawn take
            if (dest_index > 0) && (dest_index as u8 == self.get_enpassant()) {
                moves.push(BitMove::create_capture(
                    index,
                    dest_index as u8,
                    /* source_piece = */ PieceType::Pawn,
                    /* captured = */ piece_type(dest_piece),
                    None,
                    MOVE_CAPTURE,
                ));
            }
        }

        // Pawn single advance
        let dest_index = (index as i8 + (BOARD_SIZE as i8 * forward)) as usize;
        if self.get_piece(dest_index) != 0 {
            return moves;
        }
        if is_back_rank(dest_index) {
            for promote_to in PROMOTIONS {
                moves.push(BitMove::create(
                    index,
                    dest_index as u8,
                    PieceType::Pawn,
                    Some(promote_to),
                    MOVE_PROMO,
                ));
            }
        } else {
            moves.push(BitMove::create(
                index,
                dest_index as u8,
                PieceType::Pawn,
                None,
                0,
            ));
        }

        // Pawn double advance
        let base_rank = if self.white_to_move() { 6 } else { 1 };
        if (index as u32 / BOARD_SIZE) != base_rank {
            return moves;
        }
        let double = (dest_index as i8 + (BOARD_SIZE as i8 * forward)) as usize;
        if self.get_piece(double) == 0 {
            moves.push(BitMove::create(
                index,
                double as u8,
                PieceType::Pawn,
                None,
                0,
            ));
        }
        moves
    }

    fn legal_moves_general(&self, piece: PieceType, index: u8) -> Vec<BitMove> {
        let mut moves = Vec::new();
        let (is_multi_step, directions) = match piece {
            PieceType::Knight => (false, KNIGHT_DIRS),
            PieceType::Bishop => (true, BISHOP_DIRS),
            PieceType::Rook => (true, ROOK_DIRS),
            PieceType::Queen => (true, ROYAL_DIRS),
            PieceType::King => (false, ROYAL_DIRS),
            _ => (false, EMPTY),
        };
        for dir in directions {
            if dir == (0, 0) {
                continue;
            }
            let (mut dest_index, mut out_of_bounds) = index_plus_coord(index as i8, dir);
            while is_multi_step && (!out_of_bounds) && (self.get_piece(dest_index) == 0) {
                moves.push(BitMove::create(index, dest_index as u8, piece, None, 0));
                (dest_index, out_of_bounds) = index_plus_coord(dest_index as i8, dir);
            }
            if out_of_bounds {
                continue;
            }
            let dest_piece = self.get_piece(dest_index);
            if dest_piece != 0 && self.is_opponent_piece(dest_piece) {
                moves.push(BitMove::create_capture(
                    index,
                    dest_index as u8,
                    /* source_piece = */ piece,
                    /* captured = */ piece_type(dest_piece),
                    None,
                    MOVE_CAPTURE,
                ));
            } else if !is_multi_step && dest_piece == 0 {
                moves.push(BitMove::create(index, dest_index as u8, piece, None, 0));
            }
        }
        moves
    }

    pub fn legal_moves_for_piece(&self, piece: PieceType, index: u8) -> Vec<BitMove> {
        match piece {
            PieceType::Pawn => self.legal_moves_for_pawn(index),
            PieceType::Empty => Vec::new(),
            _ => self.legal_moves_general(piece, index),
        }
    }

    fn is_square_attacked_by(
        &self,
        index: u32,
        directions: [(i8, i8); 8],
        piece: PieceType,
        by_white: bool,
    ) -> bool {
        let is_multi_step = match piece {
            PieceType::Bishop => true,
            PieceType::Rook => true,
            PieceType::Queen => true,
            _ => false,
        };
        for d in directions {
            if d == (0, 0) {
                continue;
            }
            let (mut scan, mut out_of_bounds) = index_plus_coord(index as i8, d);
            while is_multi_step && !out_of_bounds && self.get_piece(scan) == 0 {
                (scan, out_of_bounds) = index_plus_coord(scan as i8, d);
            }
            if out_of_bounds {
                continue;
            }
            // println!("{:o} {} {:o}", index, piece, scan);
            let attacker = self.get_piece(scan);
            if (piece_type(attacker) == piece) && (by_white == is_piece_white(attacker)) {
                // println!("BIG HELLO");
                return true;
            }
        }
        false
    }

    pub fn is_square_attacked(&self, index: u32, by_white: bool) -> bool {
        let forward = if by_white { 1 } else { -1 };
        // println!("checking index: {}", index);
        for diag in [(forward, 1), (forward, -1)] {
            let (scan, out_of_bounds) = index_plus_coord(index as i8, diag);
            if out_of_bounds {
                continue;
            }
            let piece = self.get_piece(scan);
            if piece_type(piece) == PieceType::Pawn && (by_white == is_piece_white(piece)) {
                return true;
            }
        }
        PIECE_DIRS.iter().any(|(piece, directions)| {
            self.is_square_attacked_by(index, *directions, *piece, by_white)
        })
    }

    pub fn legal_castle_moves(&self) -> Vec<BitMove> {
        let mut moves = Vec::new();
        for shift in 0..2 {
            let mask = 1 << (shift + if self.white_to_move() { 2 } else { 0 });
            let castle = self.get_castle_rights() & mask;
            if castle == 0 {
                continue;
            }
            // Check that all squares between king and rook are empty
            let is_king_side = shift == 0;
            let sq_between = match (self.white_to_move(), is_king_side) {
                (false, false) => [1, 2, 3],
                (false, true) => [5, 6, 0],
                (true, false) => [57, 58, 59],
                (true, true) => [61, 62, 0],
            };
            let mut all_empty = true;
            for square in sq_between {
                if square == 0 {
                    continue;
                }
                if self.get_piece(square) != 0 {
                    all_empty = false;
                }
            }
            if !all_empty {
                continue;
            }

            // Check that all squares king would have to traverse are safe
            let transits = match (self.white_to_move(), is_king_side) {
                (false, false) => [2, 3, 4],
                (false, true) => [4, 5, 6],
                (true, false) => [58, 59, 60],
                (true, true) => [60, 61, 62],
            };
            if transits
                .iter()
                .any(|&t| self.is_square_attacked(t, !self.white_to_move()))
            {
                continue;
            }
            moves.push(match castle {
                // e8g8 - black king-side
                0b0001 => BitMove::create(0o04, 0o06, PieceType::King, None, MOVE_CASTLE),
                // e8c8 - black queen-side
                0b0010 => BitMove::create(0o04, 0o02, PieceType::King, None, MOVE_CASTLE),
                // e1g1 - white king-side
                0b0100 => BitMove::create(0o74, 0o76, PieceType::King, None, MOVE_CASTLE),
                // e1c1 - white queen-side
                0b1000 => BitMove::create(0o74, 0o72, PieceType::King, None, MOVE_CASTLE),
                _ => panic!("Bad castle format {}", castle),
            });
        }
        moves
    }
}
