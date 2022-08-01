use std::fs::File;
use std::io::prelude::*;

pub struct BookMovesTree {
    _count: u32,
    _children: Vec<BookMovesTree>,
}

impl BookMovesTree {
    pub fn generate_from_file() -> BookMovesTree {
        // let mut _file = match File::open("alireza_lichess.pgn") {
        //     Err(why) => panic!("couldn't open pgn file: {why}"),
        //     Ok(file) => file,
        // };

        BookMovesTree {
            _count: 1,
            _children: Vec::new(),
        }
    }
}
