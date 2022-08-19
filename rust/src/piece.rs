const PIECE_TYPE_MASK: u32 = 0b1110;
const PIECE_SIDE_MASK: u32 = 0b0001;
pub const PIECE_TYPE: u32 = 1;

#[derive(FromPrimitive, Copy, Clone, PartialEq)]
pub enum PieceType {
    Empty = 0,
    Pawn = 1,
    Knight = 2,
    Bishop = 3,
    Rook = 4,
    Queen = 5,
    King = 6,
}

pub fn piece_type(piece: u32) -> PieceType {
    num::FromPrimitive::from_u32((piece & PIECE_TYPE_MASK) >> PIECE_TYPE).unwrap()
}

pub fn is_piece_white(piece: u32) -> bool {
    (PIECE_SIDE_MASK & piece) == 1
}

pub fn piece_to_bits(piece: PieceType, side: u8) -> u8 {
    ((piece as u8) << (PIECE_TYPE as u8)) | side
}

pub fn char_to_piece(piece: char) -> u8 {
    let p_type = match piece.to_ascii_lowercase() {
        'p' => PieceType::Pawn as u8,
        'n' => PieceType::Knight as u8,
        'b' => PieceType::Bishop as u8,
        'r' => PieceType::Rook as u8,
        'q' => PieceType::Queen as u8,
        'k' => PieceType::King as u8,
        _ => PieceType::Empty as u8,
    };
    let p_side = if piece.is_lowercase() { 0 } else { 1 };
    p_side | (p_type << PIECE_TYPE)
}

pub fn piece_to_char(piece: u32, if_none: &str) -> &str {
    match (piece_type(piece), is_piece_white(piece)) {
        (PieceType::Pawn, true) => "P",
        (PieceType::Pawn, false) => "p",
        (PieceType::Knight, true) => "N",
        (PieceType::Knight, false) => "n",
        (PieceType::Bishop, true) => "B",
        (PieceType::Bishop, false) => "b",
        (PieceType::Rook, true) => "R",
        (PieceType::Rook, false) => "r",
        (PieceType::Queen, true) => "Q",
        (PieceType::Queen, false) => "q",
        (PieceType::King, true) => "K",
        (PieceType::King, false) => "k",
        _ => if_none,
    }
}
