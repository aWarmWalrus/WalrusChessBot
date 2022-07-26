extern crate num;
#[macro_use]
extern crate num_derive;

mod bitboard;

use bitboard::ArrayBoard;
use bitboard::BitMove;

fn main() {
    let mut board = ArrayBoard::create_from_fen(bitboard::STARTING_FEN);
    board = board.make_move(BitMove::from_move("e2e4"));
    board = board.make_move(BitMove::from_move("e7e5"));
    board = board.make_move(BitMove::from_move("g2g8"));
    board.pretty_print(true);
    board = board.make_move(BitMove::from_move("b7b1"));
    board.pretty_print(true);
}
