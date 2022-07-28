use super::arrayboard::{ArrayBoard, BitMove, STARTING_FEN};
use super::engine;
use std::io;

pub fn run() {
    let mut board: Option<ArrayBoard> = None;
    loop {
        let mut buffer = String::new();
        io::stdin().read_line(&mut buffer);
        let instructions: Vec<&str> = buffer.split_whitespace().collect();
        match instructions[0] {
            "uci" => {
                println!("id name walrus-bot");
                println!("id author The Walrus");
                println!("uciok");
            }
            "setoption" => {
                println!("unimplemented");
            }
            "ucinewgame" => {
                println!("unimplemented");
            }
            "isready" => {
                println!("readyok");
            }
            "position" => {
                board = match instructions[1] {
                    "fen" => Some(ArrayBoard::create_from_fen(
                        instructions[2..8].join(" ").as_str(),
                    )),
                    "startpos" => {
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
                match board {
                    Some(b) => {
                        let (best, nodes) = engine::search(
                            b,
                            /* alpha= */ i64::MIN,
                            /* beta= */ i64::MAX,
                            /* depth=*/ 0,
                        );
                        match best {
                            Some(mv) => println!("bestmove {}", mv.to_string()),
                            None => {
                                b.pretty_print(true);
                                println!("ERROR: no moves possible");
                            }
                        }
                    }
                    None => println!("ERROR: No board has been initialized yet. Use 'position'."),
                };
            }
            "print" => {
                match board {
                    Some(b) => {
                        b.pretty_print(true);
                        b.print_legal_moves();
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
