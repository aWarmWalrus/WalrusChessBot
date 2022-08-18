use crate::arrayboard::{algebraic_to_index, index_to_algebraic};
use crate::piece::PieceType;

#[derive(Copy, Clone)]
pub struct BitMove {
    pub source_square: u8,
    pub dest_square: u8,
    pub promote_to: Option<PieceType>,
    pub meta: u16,
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
