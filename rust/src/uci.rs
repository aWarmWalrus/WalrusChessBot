use crate::arrayboard::{ArrayBoard, STARTING_FEN};
use crate::book_moves::BookMoves;
use crate::chessboard::ChessBoard;
use crate::engine;
use crate::logging;
use crate::moves::BitMove;
use std::cmp;
use std::collections::HashMap;
use std::io;
use std::sync::atomic::Ordering;
use std::time::Instant;

pub fn go(
    board: &mut impl ChessBoard,
    book_moves_opt: &Option<&BookMoves>,
    wtime: Option<u32>,
    btime: Option<u32>,
    setup: &str,
) {
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

    let time_left = if board.white_to_move() && wtime.is_some() {
        wtime.unwrap()
    } else if !board.white_to_move() && btime.is_some() {
        btime.unwrap()
    } else {
        0
    };
    if time_left == 0 || board.get_move_number() < 14 {
        // don't change max depth
    } else if time_left <= 15000 {
        engine::MAX_DEPTH.store(5, Ordering::Relaxed); // less than 15 sec
    } else if time_left <= 120000 {
        engine::MAX_DEPTH.store(6, Ordering::Relaxed); // less than 2 min
    } else if time_left <= 600000 {
        engine::MAX_DEPTH.store(7, Ordering::Relaxed); // less than 10 min
    } else if time_left <= 1800000 {
        // less than 30 min. Don't spend too much time at the beginning of the game.
        if board.get_move_number() > 20 {
            engine::MAX_DEPTH.store(8, Ordering::Relaxed);
        } else {
            engine::MAX_DEPTH.store(7, Ordering::Relaxed);
        }
    } else {
        if board.get_move_number() > 30 {
            engine::MAX_DEPTH.store(9, Ordering::Relaxed);
        } else {
            engine::MAX_DEPTH.store(8, Ordering::Relaxed);
        }
    }

    let start = Instant::now();
    match engine::search(
        board,
        /* alpha= */ i32::MIN as i64,
        /* beta= */ i32::MAX as i64,
        /* depth=*/ 0,
    ) {
        Ok((best, score, nodes)) => {
            let tm = start.elapsed().as_millis();
            println!(
                "info nodes {nodes} time {tm} nps {}",
                (nodes as f64 / (tm as f64 / 1000.0)) as u64
            );
            if best.is_empty() {
                board.pretty_print(true);
                println!("ERROR: no moves possible");
                logging::record_move(
                    board.get_move_number(),
                    engine::MAX_DEPTH.load(Ordering::Relaxed),
                    tm as u64,
                    nodes,
                    score,
                    "",
                    &board.get_all_pieces(),
                    setup,
                );
            } else {
                let bestmove = best.split_whitespace().nth(0).unwrap();
                println!("bestmove {bestmove}");
                logging::record_move(
                    board.get_move_number(),
                    engine::MAX_DEPTH.load(Ordering::Relaxed),
                    tm as u64,
                    nodes,
                    score,
                    bestmove,
                    &board.get_all_pieces(),
                    setup,
                );
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
    let mut setup = String::new();

    let mut board_opt: Option<ArrayBoard> = None;
    loop {
        let mut buffer = String::new();
        let result = io::stdin().read_line(&mut buffer);
        if result.is_err() {
            println!("{:?}", result.err());
            continue;
        }
        let instr_cp = buffer.clone();
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
                engine::MAX_DEPTH.store(engine::INIT_DEPTH, Ordering::Relaxed);
            }
            "isready" => {
                println!("readyok");
            }
            "p" | "position" => {
                setup = String::from(instr_cp.trim());
                book_moves_tracker = Some(&book_moves_root);
                board_opt = match instructions[1] {
                    "fen" => {
                        book_moves_tracker = None;
                        Some(ArrayBoard::create_from_fen(
                            instructions[2..].join(" ").as_str(),
                        ))
                    }
                    "sp" | "startpos" => {
                        let mut board = ArrayBoard::create_from_fen(STARTING_FEN);
                        if instructions.len() > 3 {
                            instructions[3..].iter().for_each(|mv| {
                                book_moves_tracker = match book_moves_tracker {
                                    Some(bm) => bm.get_child(mv),
                                    None => None,
                                };
                                if let Err(e) = board.make_move(&mut BitMove::from_string(mv)) {
                                    panic!("{}", e);
                                }
                            });
                        }
                        Some(board)
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
                        go(board, &book_moves_tracker, wtime, btime, &setup);
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
