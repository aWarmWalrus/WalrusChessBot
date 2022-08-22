use super::arrayboard::{ArrayBoard, BitMove, STARTING_FEN};
use super::book_moves::BookMoves;
use super::engine;
use std::cmp;
use std::collections::HashMap;
use std::io;
use std::sync::atomic::Ordering;
use std::time::Instant;

fn go(
    board_opt: Option<ArrayBoard>,
    book_moves_opt: &Option<&BookMoves>,
    wtime: Option<u32>,
    btime: Option<u32>,
) {
    if board_opt.is_none() {
        println!("ERROR: No board has been initialized yet. Use 'position'.");
        return;
    }
    if let Some(book_moves) = book_moves_opt {
        let best_move = book_moves.pick_weighted_random();
        match best_move {
            Some(mv) => {
                println!("bestmove {}", mv);
                return;
            }
            None => println!("DEBUG: out of book moves, need to actually think now"),
        }
    }

    let board = board_opt.unwrap();
    if board.white_to_move() && let Some(time_left) = wtime {
        if time_left <= 30000 {
            engine::MAX_DEPTH.store(4, Ordering::Relaxed);
        } else if time_left <= 60000 {
            engine::MAX_DEPTH.store(5, Ordering::Relaxed);
        } else if time_left <= 300000 {
            engine::MAX_DEPTH.store(6, Ordering::Relaxed);
        } else {
            engine::MAX_DEPTH.store(7, Ordering::Relaxed);
        }
    } else if !board.white_to_move() && let Some(time_left) = btime {
        if time_left <= 30000 {
            engine::MAX_DEPTH.store(4, Ordering::Relaxed);
        } else if time_left <= 60000 {
            engine::MAX_DEPTH.store(5, Ordering::Relaxed);
        } else if time_left <= 300000 {
            engine::MAX_DEPTH.store(6, Ordering::Relaxed);
        } else {
            engine::MAX_DEPTH.store(7, Ordering::Relaxed);
        }
    }

    let start = Instant::now();
    match engine::search(
        board,
        /* alpha= */ i32::MIN as i64,
        /* beta= */ i32::MAX as i64,
        /* depth=*/ 0,
    ) {
        Ok((best, _score, nodes)) => {
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
        Err(e) => {
            panic!("{}", e);
        }
    }
}

pub fn run() {
    let book_moves_root: BookMoves = BookMoves::generate_from_file();
    let mut book_moves_tracker: Option<&BookMoves> = Some(&book_moves_root);

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
                println!(
                    "option name MaxDepth type spin default {} min 1 max 10",
                    engine::MAX_DEPTH.load(Ordering::Relaxed)
                );
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
                book_moves_tracker = Some(&book_moves_root);
            }
            "isready" => {
                println!("readyok");
            }
            "p" | "position" => {
                book_moves_tracker = Some(&book_moves_root);
                board_opt = match instructions[1] {
                    "fen" => {
                        book_moves_tracker = None;
                        Some(ArrayBoard::create_from_fen(
                            instructions[2..].join(" ").as_str(),
                        ))
                    }
                    "sp" | "startpos" => {
                        let mut nb = ArrayBoard::create_from_fen(STARTING_FEN);
                        if instructions.len() > 3 {
                            nb = instructions[3..].iter().fold(nb, |old_board, mv| {
                                book_moves_tracker = match book_moves_tracker {
                                    Some(bm) => bm.get_child(mv),
                                    None => None,
                                };
                                if let Err(e) = board.make_move(&mut BitMove::from_string(mv)) {
                                    panic!("{}", e);
                                }
                                // hist_data.push(board.get_hash());
                            });
                            // CODE SMELL ALERT. Pop last one off, since the first thing we do in
                            // the search is to increment the given board state.
                            // hist_data.pop();
                        }
                        Some(nb)
                    }
                    _ => None,
                };
            }
            "go" => {
                let (mut wtime, mut btime): (Option<u32>, Option<u32>) = (None, None);
                if instructions.len() >= 5
                    && instructions[1] == "wtime"
                    && instructions[3] == "btime"
                {
                    wtime = Some(instructions[2].parse::<u32>().unwrap());
                    btime = Some(instructions[4].parse::<u32>().unwrap());
                }
                match &mut board_opt {
                    None => {
                        println!("ERROR: No board has been initialized yet. Use 'position'.");
                    }
                    Some(board) => {
                        go(board, &book_moves_tracker, wtime, btime);
                    }
                }
            }
            "print" => {
                match &board_opt {
                    Some(b) => {
                        b.pretty_print(true);
                        b.print_legal_moves(false);
                    }
                    None => println!("ERROR: No board has been initialized yet. Use 'position'."),
                };
                match book_moves_tracker {
                    Some(bm) => bm.print_children(),
                    None => (),
                }
            }
            "exit" | "end" | "quit" => break,
            _ => (),
        }
    }
}
