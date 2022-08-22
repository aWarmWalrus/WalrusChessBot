#![feature(test)]
#![allow(unused_imports)]
extern crate num;
extern crate test;
#[macro_use]
extern crate num_derive;

mod arrayboard;
mod book_moves;
mod engine;
mod moves;
mod piece;
mod uci;

use arrayboard::ArrayBoard;
use chessboard::ChessBoard;
use moves::BitMove;
use piece::PieceType;
use rand::Rng;
use std::time::Instant;
use test::Bencher;

const DO_DEBUG: bool = false;
const DO_PERFT: bool = false;

const _TEST_CASE_1: &str = "position startpos moves e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 b8c6 b1c3 d8c7 d1d3 c6d4 d3d4 c7b6 d4b6 a7b6 c3b5 a8a4 f2f3 f8c5 c2c3 e8f8 b2b3";

fn perft(
    board: &mut impl ChessBoard,
    max_depth: u32,
    depth: u32,
) -> Result<(u32, u32, u32, u32, u32), String> {
    let (mut nodes, mut captures, mut castles, mut checks, mut promos) = (0, 0, 0, 0, 0);
    if depth == max_depth {
        nodes += 1;
        if board.is_king_checked() {
            checks += 1;
        }
        return Ok((nodes, captures, castles, checks, promos));
    }
    for mut mv in board.generate_moves() {
        match board.make_move(&mut mv) {
            Ok(true) => match perft(board, max_depth, depth + 1) {
                Ok((n, c1, c2, c3, p)) => {
                    nodes += n;
                    captures += c1;
                    castles += c2;
                    checks += c3;
                    promos += p;
                }
                Err(mut e) => {
                    println!("Move made: {}", mv.to_string());
                    board.pretty_print(true);
                    board.take_back_move(&mv);
                    e.push(' ');
                    e.push_str(&mv.to_string());
                    return Err(e);
                }
            },
            Ok(false) => (),
            Err(mut e) => {
                board.take_back_move(&mv);
                e.push(' ');
                e.push_str(&mv.to_string());
                return Err(e);
            }
        }
        board.take_back_move(&mv);
    }
    Ok((nodes, captures, castles, checks, promos))
}

fn main() {
    if DO_DEBUG {
        let mut board = ArrayBoard::create_from_fen(arrayboard::STARTING_FEN);
        board.pretty_print(true);
        let mut mv_w = BitMove::create(0o64, 0o54, PieceType::Pawn, None, 0);
        let mut mv_b = BitMove::create(0o10, 0o20, PieceType::Pawn, None, 0);
        let mut mv_w1 = BitMove::create(0o63, 0o53, PieceType::Pawn, None, 0);
        let mut mv_b1 = BitMove::create(0o11, 0o21, PieceType::Pawn, None, 0);

        board.make_move(&mut mv_w1);
        board.make_move(&mut mv_b1);
        board.make_move(&mut mv_w);
        board.make_move(&mut mv_b);
        board.pretty_print(true);

        board.take_back_move(&mut mv_b);
        board.pretty_print(true);
        board.take_back_move(&mut mv_w);
        board.pretty_print(true);
        board.take_back_move(&mut mv_b1);
        board.pretty_print(true);
        board.take_back_move(&mut mv_w1);
        board.pretty_print(true);

        // UNCOMMENT THIS IF YOU WANT MORE RANDOM NUMBERS
        // let mut rng = rand::thread_rng();
        // for _ in 0..16 {
        //     println!("{},", rng.gen::<u64>());
        // }
    } else if DO_PERFT {
        let mut board = ArrayBoard::create_from_fen(arrayboard::STARTING_FEN);
        let start = Instant::now();
        let depth = 6;
        let (nodes, captures, castles, checks, promos) = perft(&mut board, depth, 0).unwrap();
        let tm = start.elapsed().as_millis();
        println!(
            "Perft({depth}) results: \n    \
             nodes: {nodes}\n    \
             captures: {captures}\n    \
             castles: {castles}\n    \
             checks: {checks}\n    \
             promos: {promos}\n    \
             {:?}ms,  {:.2} nps",
            tm,
            (1000.0 * nodes as f64) / tm as f64
        );
    } else {
        println!("=============================================================");
        println!("====           W A L R U S       B O T                   ====");
        println!("=============================================================");
        uci::run();
    }
}

#[bench]
fn init_fen_basic(b: &mut Bencher) {
    b.iter(|| ArrayBoard::create_from_fen(arrayboard::STARTING_FEN));
}

#[bench]
fn init_fen_tricky(b: &mut Bencher) {
    b.iter(|| ArrayBoard::create_from_fen(arrayboard::TRICKY_FEN));
}

#[bench]
fn init_startpos_50_moves(b: &mut Bencher) {
    let moves50 = "h2h3 a7a6 e2e3 h7h5 d1e2 d7d6 e2h5 b7b6 h5d1 c8g4 f1d3 c7c5 f2f4 h8h5 h3g4 g7g5 e1f1 f8g7 h1h4 g7h8 f4g5 d8d7 g4h5 f7f5 h4h2 a8a7 d1g4 b8c6 c2c3 a7a8 d3c4 c6b4 c4e6 e8f8 d2d3 f8e8 e6f5 d7c6 g1f3 c6d5 g4f4 d5d4 f5h3 e7e6 b1d2 b4d5 h2h1 c5c4 f4f8 e8f8 f1g1 a6a5 a2a4 d5c3 g2g3 c4d3 h3f5 f8e7 f5h7 d4a4 g1f2 e7d8 h1f1 c3a2 b2b4 b6b5 f1e1 e6e5 f3d4 a4c2 e1f1 c2b3 g3g4 b3d5 h7e4 a5b4 e4h1 h8f6 d2b3 d8d7 h1d5 a8a5 f2g3 a2c1 g3h2 a5a8 f1h1 f6d8 h2g2 d8g5 h1e1 g5h6 a1a8 c1e2 d4e6 g8f6 a8a5 f6e8 e1d1".split(' ');

    b.iter(|| {
        let mut board = ArrayBoard::create_from_fen(arrayboard::STARTING_FEN);
        for mv in moves50.clone() {
            if let Err(e) = board.make_move(&mut BitMove::from_string(mv)) {
                panic!("{}", e);
            };
        }
    });
}

#[bench]
fn init_startpos_100_moves(b: &mut Bencher) {
    let moves100 = "h2h3 a7a6 e2e3 h7h5 d1e2 d7d6 e2h5 b7b6 h5d1 c8g4 f1d3 c7c5 f2f4 h8h5 h3g4 g7g5 e1f1 f8g7 h1h4 g7h8 f4g5 d8d7 g4h5 f7f5 h4h2 a8a7 d1g4 b8c6 c2c3 a7a8 d3c4 c6b4 c4e6 e8f8 d2d3 f8e8 e6f5 d7c6 g1f3 c6d5 g4f4 d5d4 f5h3 e7e6 b1d2 b4d5 h2h1 c5c4 f4f8 e8f8 f1g1 a6a5 a2a4 d5c3 g2g3 c4d3 h3f5 f8e7 f5h7 d4a4 g1f2 e7d8 h1f1 c3a2 b2b4 b6b5 f1e1 e6e5 f3d4 a4c2 e1f1 c2b3 g3g4 b3d5 h7e4 a5b4 e4h1 h8f6 d2b3 d8d7 h1d5 a8a5 f2g3 a2c1 g3h2 a5a8 f1h1 f6d8 h2g2 d8g5 h1e1 g5h6 a1a8 c1e2 d4e6 g8f6 a8a5 f6e8 e1d1 d3d2 d1g1 e2c1 g2f1 d2d1n d5a8 e5e4 f1g2 d6d5 g1e1 d7c8 g2g1 h6f4 a8d5 c8b8 d5e4 d1e3 e1d1 f4c7 h5h6 c7a5 b3a1 e8d6 e4c6 e3f5 d1f1 c1d3 g4g5 f5d4 e6c7 d6e8 f1f3 d4c2 c6d7 c2e1 f3d3 e8d6 c7b5 e1c2 d3f3 d6b5 d7b5 a5d8 g1h1 d8a5 f3g3 c2d4 g3h3 b8c8 g5g6 a5b6 h3b3 d4c6 b3d3 c6e7 d3d2 c8c7 d2f2 e7c6 f2f8 b6e3 f8f3 e3g1 f3g3 g1c5 h1h2 c6d4 g3e3 d4f5 h6h7 c5e7 b5d3 f5d4 h7h8b e7g5 e3e8 d4c2 e8g8 b4b3 g8a8 c7b6 h8f6 g5d2 a8a3 b6c5 a3a6 b3b2 h2g3 c2a3 a6b6 b2b1r d3f5 b1b5 g3h2 b5b4 f6h4 c5d5 h2g3 b4b5 f5h3".split(' ');

    b.iter(|| {
        let mut board = ArrayBoard::create_from_fen(arrayboard::STARTING_FEN);
        for mv in moves100.clone() {
            if let Err(e) = board.make_move(&mut BitMove::from_string(mv)) {
                panic!("{}", e);
            }
        }
    });
}

#[bench]
fn perft_depth_3(b: &mut Bencher) {
    b.iter(|| {
        let mut board = ArrayBoard::create_from_fen(arrayboard::STARTING_FEN);
        if let Err(e) = perft(&mut board, 3, 0) {
            panic!("{}", e);
        }
    });
}
