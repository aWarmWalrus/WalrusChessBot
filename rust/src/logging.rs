use std::fs::File;
use std::io::{prelude::*, BufReader};

pub fn record_move(
    ply: u32,
    depth: u8,
    time: u64,
    nodes: u64,
    score: i64,
    best_move: &str,
    pieces: &str,
    uci_instr: &str,
) {
    let mut log_file = match File::options().append(true).create(true).open("logs.csv") {
        Ok(f) => f,
        Err(e) => panic!("Couldn't open log_file: {e}"),
    };
    match log_file.write_fmt(format_args!(
        "{ply},{depth},{time},{nodes},{score},{best_move},{pieces},{uci_instr}\n"
    )) {
        Err(e) => panic!("Couldn't write log to log file: {e}"),
        _ => (),
    };
    // File::open(OpenOptions::)
}
