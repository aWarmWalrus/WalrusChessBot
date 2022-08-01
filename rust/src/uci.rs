use super::arrayboard::{ArrayBoard, BitMove, STARTING_FEN};
use super::book_moves;
use super::engine;
use std::cmp;
use std::io;
use std::sync::atomic::Ordering;
use std::time::Instant;

pub fn run() {
    let _book: book_moves::BookMovesTree = book_moves::BookMovesTree::generate_from_file();

    let mut board_opt: Option<ArrayBoard> = None;
    loop {
        let mut buffer = String::new();
        let result = io::stdin().read_line(&mut buffer);
        if result.is_err() {
            println!("{:?}", result.err());
        }
        let instructions: Vec<&str> = buffer.split_whitespace().collect();
        if instructions.len() == 0 {
            continue;
        }
        match instructions[0] {
            "uci" => {
                println!("id name walrus-bot");
                println!("id author The Walrus");
                println!("option name MaxDepth type spin default 7 min 1 max 10");
                println!("uciok");
            }
            "setoption" => {
                if instructions[1] == "name"
                    && instructions[2] == "MaxDepth"
                    && instructions[3] == "value"
                {
                    engine::MAX_DEPTH.store(
                        instructions[4].parse::<u8>().unwrap_or_default(),
                        Ordering::Relaxed,
                    );
                }
            }
            "ucinewgame" => {
                ()
            }
            "isready" => {
                println!("readyok");
            }
            "p" | "position" => {
                board_opt = match instructions[1] {
                    "fen" => Some(ArrayBoard::create_from_fen(
                        instructions[2..].join(" ").as_str(),
                    )),
                    "sp" | "startpos" => {
                        let mut nb = ArrayBoard::create_from_fen(STARTING_FEN);
                        if instructions.len() > 3 {
                            nb = instructions[3..].iter().fold(nb, |board_acc, mv| {
                                board_acc.make_move(&BitMove::from_string(mv))
                            });
                            // for mv in instructions[3..].iter() {
                            //     new_board = new_board.make_move(&BitMove::from_string(mv));
                            // }
                        }
                        Some(nb)
                    }
                    _ => None,
                };
            }
            "go" => {
                match board_opt {
                    Some(board) => {
                        let start = Instant::now();
                        let (best, _score, _mate_in, nodes) = engine::search(
                            board,
                            /* alpha= */ i32::MIN as i64,
                            /* beta= */ i32::MAX as i64,
                            /* depth=*/ 0,
                        );
                        let tm = start.elapsed().as_millis();
                        println!(
                            "info nodes {nodes} time {tm} nps {}",
                            (nodes as f64 / (tm as f64 / 1000.0)) as u64
                        );
                        if best.is_empty() {
                            board.pretty_print(true);
                            println!("ERROR: no moves possible");
                        } else {
                            println!("bestmove {}", best.split_whitespace().nth(0).unwrap());
                        }
                    }
                    None => println!("ERROR: No board has been initialized yet. Use 'position'."),
                };
            }
            "print" => {
                match board_opt {
                    Some(b) => {
                        b.pretty_print(true);
                        b.print_legal_moves(false);
                    }
                    None => println!("ERROR: No board has been initialized yet. Use 'position'."),
                };
            }
            "exit" | "end" | "quit" => break,
            _ => (),
        }
    }
}
