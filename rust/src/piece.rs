const PIECE_TYPE_MASK: u32 = 0b1110;
const PIECE_SIDE_MASK: u32 = 0b0001;
pub const PIECE_TYPE: u32 = 1;

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

pub fn is_piece_white(piece: u32) -> bool {
    (PIECE_SIDE_MASK & piece) == 1
}

pub fn piece_to_bits(piece: PieceType, side: u8) -> u8 {
    ((piece as u8) << (PIECE_TYPE as u8)) | side
}
