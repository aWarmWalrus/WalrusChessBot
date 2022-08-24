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

    // Only moves that are generated during search will have the source_piece and captured fields
    // filled in. This information is only stored in this struct to help in taking back moves.
    pub source_piece: PieceType,
    pub captured: PieceType,

    pub promote_to: Option<PieceType>,

    // Meta bits about the move, that are used to sort moves.
    // Bits 0-7 are the score for measuring Most Valuable Victim / Least Valuable Attacker.
    // Bits 8-11 are for categorizing the moves (capture, check, castle, promo).
    pub meta: u16,

    // Only moves that are generated during search will use this field. This is only stored here
    // to help in taking back moves and restoring prior state.
    pub prior_castle_rights: u8,
    pub prior_enpassant: u8,
}

impl BitMove {
    pub fn is_capture(&self) -> bool {
        self.meta & MOVE_CAPTURE > 0
    }

    pub fn _is_check(&self) -> bool {
        self.meta & MOVE_CHECK > 0
    }

    pub fn _is_castle(&self) -> bool {
        self.meta & MOVE_CASTLE > 0
    }

    pub fn _is_promo(&self) -> bool {
        self.meta & MOVE_PROMO > 0
    }

    pub fn set_prior_castle_rights(&mut self, cr: u8) {
        self.prior_castle_rights = cr;
    }

    pub fn set_prior_enpassant(&mut self, ep: u8) {
        self.prior_enpassant = ep;
    }

    pub fn get_prior_castle_rights(&self) -> u8 {
        self.prior_castle_rights
    }

    pub fn get_prior_enpassant(&self) -> u8 {
        self.prior_enpassant
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
            prior_castle_rights: 0,
            prior_enpassant: 0,
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
            prior_castle_rights: 0,
            prior_enpassant: 0,
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
        // If a promoted pawn captures, use the promotion as the "attacker" instead of the pawn.
        let attacker = match promote_to {
            Some(piece) => piece,
            None => source_piece,
        };
        // Most Valuable Victim / Least Valuable Attacker
        let capture_cost = if captured != PieceType::Empty {
            captured as u16 * 10 - attacker as u16
        } else {
            0
        };
        BitMove {
            source_square,
            dest_square,
            source_piece,
            captured,
            promote_to,
            meta: meta | capture_cost,
            prior_castle_rights: 0,
            prior_enpassant: 0,
        }
    }
}
