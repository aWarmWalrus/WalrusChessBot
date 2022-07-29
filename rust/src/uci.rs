use super::arrayboard::{ArrayBoard, BitMove, STARTING_FEN};
use super::engine;
use std::cmp;
use std::io;
use std::time::Instant;

pub fn run() {
    let mut board_opt: Option<ArrayBoard> = None;
    unsafe {
        engine::initialize_tables();
    }
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
                println!("option name MaxDepth type spin default 5 min 1 max 10");
                println!("uciok");
            }
            "setoption" => {
                if instructions[1] == "name"
                    && instructions[2] == "MaxDepth"
                    && instructions[3] == "value"
                {
                    unsafe {
                        engine::MAX_DEPTH = instructions[4].parse().unwrap_or_default();
                    }
                }
            }
            "ucinewgame" => {
                println!("unimplemented");
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
            "go" => unsafe {
                match board_opt {
                    Some(board) => {
                        let start = Instant::now();
                        let (best, _score, nodes) = engine::search(
                            board,
                            /* alpha= */ i64::MIN,
                            /* beta= */ i64::MAX,
                            /* depth=*/ 0,
                        );
                        match best {
                            Some(mv) => println!("bestmove {}", mv.to_string()),
                            None => {
                                board.pretty_print(true);
                                println!("ERROR: no moves possible");
                            }
                        }
                        let tm = start.elapsed().as_millis();
                        println!(
                            "info nodes {nodes} time {tm} nps {}",
                            nodes as u128 / cmp::max(tm / 1000, 1)
                        );
                    }
                    None => println!("ERROR: No board has been initialized yet. Use 'position'."),
                };
            },
            "print" => {
                match board_opt {
                    Some(b) => {
                        b.pretty_print(true);
                        b.print_legal_moves(false);
                    }
                    None => println!("ERROR: No board has been initialized yet. Use 'position'."),
                };
            }
            "exit" => break,
            "end" => break,
            "quit" => break,
            _ => (),
        }
    }
}
