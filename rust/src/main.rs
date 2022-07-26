extern crate num;
#[macro_use]
extern crate num_derive;

mod bitboard;

use bitboard::ArrayBoard;
use bitboard::BitMove;

fn main() {
    let mut board = ArrayBoard::create_from_fen(bitboard::STARTING_FEN);
    board.pretty_print(true);
    board = board.make_move(BitMove::from_string("e2e4"));
    board = board.make_move(BitMove::from_string("e7e5"));
    board = board.make_move(BitMove::from_string("g1f3"));
    board = board.make_move(BitMove::from_string("g8f6"));
    board = board.make_move(BitMove::from_string("f1e2"));
    board = board.make_move(BitMove::from_string("f8e7"));
    board = board.make_move(BitMove::from_string("a2a8"));
    board.pretty_print(true);
    board = board.make_move(BitMove::from_string("a7a1"));
    board.pretty_print(true);
}
