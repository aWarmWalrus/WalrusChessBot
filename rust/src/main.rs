extern crate num;
#[macro_use]
extern crate num_derive;

mod arrayboard;

use arrayboard::ArrayBoard;
use arrayboard::BitMove;

fn main() {
    let mut board = ArrayBoard::create_from_fen(arrayboard::STARTING_FEN);
    board = board.make_move(BitMove::from_string("e2e4"));
    board = board.make_move(BitMove::from_string("e7e5"));
    board = board.make_move(BitMove::from_string("g1f3"));
    board = board.make_move(BitMove::from_string("d7d6"));
    board = board.make_move(BitMove::from_string("f1e2"));
    board = board.make_move(BitMove::from_string("b8c6"));
    board = board.make_move(BitMove::from_string("f3h4"));
    board = board.make_move(BitMove::from_string("c8d7"));
    board = board.make_move(BitMove::from_string("h4f3"));
    board = board.make_move(BitMove::from_string("d8e7"));
    board = board.make_move(BitMove::from_string("f3h4"));
    board.pretty_print(true);
    board.print_legal_moves();
    // board.pretty_print(true);
    // board.pretty_print(true);
}
