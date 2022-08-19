use crate::arrayboard::{ArrayBoard, STARTING_FEN};
use crate::book_moves::BookMoves;
use crate::chessboard::ChessBoard;
use crate::engine;
use crate::moves::BitMove;
use std::cmp;
use std::collections::HashMap;
use std::io;
use std::sync::atomic::Ordering;
use std::time::Instant;

fn go(
    board: &mut impl ChessBoard,
    book_moves_opt: &Option<&BookMoves>,
    hist_data: &mut HashMap<u64, u8>,
    wtime: Option<u32>,
    btime: Option<u32>,
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

    if board.white_to_move() && let Some(time_left) = wtime {
        if time_left < 30000 {
            engine::MAX_DEPTH.store(4, Ordering::Relaxed);
        } else if time_left > 45000 && time_left < 360000 {
            engine::MAX_DEPTH.store(6, Ordering::Relaxed);
        } else if time_left > 600000 {
            engine::MAX_DEPTH.store(7, Ordering::Relaxed);
        }
    } else if !board.white_to_move() && let Some(time_left) = btime {
        if time_left < 30000 {
            engine::MAX_DEPTH.store(4, Ordering::Relaxed);
        } else if time_left > 45000 && time_left < 360000 {
            engine::MAX_DEPTH.store(6, Ordering::Relaxed);
        } else if time_left > 600000 {
            engine::MAX_DEPTH.store(7, Ordering::Relaxed);
        }
    }

    let start = Instant::now();
    if let Some((best, _score, nodes)) = engine::search(
        board,
        /* alpha= */ i32::MIN as i64,
        /* beta= */ i32::MAX as i64,
        /* depth=*/ 0,
        hist_data,
    ) {
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
    } else {
        panic!("ILLEGAL MOVESASAASDF");
    }
}

pub fn run() {
    let book_moves_root: BookMoves = BookMoves::generate_from_file();
    let mut book_moves_tracker: Option<&BookMoves> = Some(&book_moves_root);

    let mut board_opt: Option<ArrayBoard> = None;
    let mut hist_data: HashMap<u64, u8> = HashMap::new();
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
                hist_data.clear();
            }
            "isready" => {
                println!("readyok");
            }
            "p" | "position" => {
                hist_data.clear();
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
                                board.make_move(&mut BitMove::from_string(mv));
                                let hash = board.hash();
                                if hist_data.contains_key(&hash) {
                                    *hist_data.get_mut(&hash).unwrap() += 1;
                                } else {
                                    hist_data.insert(hash, 1);
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
                if board_opt.is_none() {
                    println!("ERROR: No board has been initialized yet. Use 'position'.");
                    return;
                }
                go(
                    &mut board_opt.unwrap(),
                    &book_moves_tracker,
                    &mut hist_data,
                    wtime,
                    btime,
                );
            }
            "print" => {
                match board_opt {
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
