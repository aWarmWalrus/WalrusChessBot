use crate::arrayboard::{algebraic_to_index, index_to_algebraic};
use crate::piece::PieceType;

// Move meta bits
pub const MOVE_CAPTURE: u16 = 0b0000100000000;
pub const MOVE_CHECK: u16 = 0b0001000000000;
pub const MOVE_CASTLE: u16 = 0b0010000000000;
pub const MOVE_PROMO: u16 = 0b0100000000000;

#[derive(Copy, Clone)]
pub struct BitMove {
    pub source_square: u8,
    pub dest_square: u8,
    pub source_piece: PieceType,
    pub captured: PieceType,
    pub promote_to: Option<PieceType>,
    // Bits 0-7 are the score for measuring Most Valuable Victim / Least Valuable Attacker.
    // Bits 8-11 are for categorizing the moves (capture, check, castle, promo).
    pub meta: u16,
    pub board_meta: u16,
}

impl BitMove {
    pub fn is_capture(&self) -> bool {
        self.meta & MOVE_CAPTURE > 0
    }

    pub fn is_check(&self) -> bool {
        self.meta & MOVE_CHECK > 0
    }

    pub fn is_castle(&self) -> bool {
        self.meta & MOVE_CASTLE > 0
    }

    pub fn is_promo(&self) -> bool {
        self.meta & MOVE_PROMO > 0
    }

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
            source_piece: PieceType::Empty,
            captured: PieceType::Empty,
            promote_to,
            meta: 0,
            board_meta: 0,
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
        source_piece: PieceType,
        promote_to: Option<PieceType>,
        meta: u16,
    ) -> BitMove {
        BitMove {
            source_square,
            dest_square,
            source_piece,
            captured: PieceType::Empty,
            promote_to,
            meta,
            board_meta: 0,
        }
    }

    pub fn create_capture(
        source_square: u8,
        dest_square: u8,
        source_piece: PieceType,
        captured: PieceType,
        promote_to: Option<PieceType>,
        meta: u16,
    ) -> BitMove {
        BitMove {
            source_square,
            dest_square,
            source_piece,
            captured,
            promote_to,
            // Most Valuable Victim / Least Valuable Attacker
            meta: meta | (captured as u16 * 10 - source_piece as u16),
            board_meta: 0,
        }
    }
}
