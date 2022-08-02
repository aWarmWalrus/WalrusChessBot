use rand::distributions::WeightedIndex;
use rand::prelude::*;
use std::collections::{HashMap, VecDeque};
use std::fs::File;
use std::io::{prelude::*, BufReader};
use std::str::SplitWhitespace;

pub struct BookMoves {
    count: u32,
    children: HashMap<String, BookMoves>,
    move_str: String,
}

impl BookMoves {
    fn add_moves_to_child(&mut self, moves: &mut VecDeque<&str>) {
        match moves.pop_front() {
            Some(mv) => match self.children.get_mut(mv) {
                Some(child) => {
                    child.count += 1;
                    child.add_moves_to_child(moves);
                }
                None => {
                    self.children.insert(
                        String::from(mv),
                        BookMoves {
                            count: 1,
                            children: HashMap::new(),
                            move_str: String::from(mv),
                        },
                    );
                }
            },
            None => (),
        }
    }

    pub fn generate_from_file() -> BookMoves {
        let file = match File::open("lichess_alireza.alg") {
            Ok(file) => file,
            Err(why) => panic!("couldn't open pgn file: {why}"),
        };
        let reader = BufReader::new(file);

        let mut book_moves_root: BookMoves = BookMoves {
            count: 1,
            children: HashMap::new(),
            move_str: String::from(""),
        };

        for line in reader.lines() {
            book_moves_root.add_moves_to_child(&mut line.unwrap().split_whitespace().collect());
        }

        book_moves_root
    }

    pub fn get_child(&self, mv: &str) -> Option<&BookMoves> {
        match self.children.get(mv) {
            Some(c) => Some(c),
            None => None,
        }
    }

    pub fn pick_weighted_random(&self) -> Option<&String> {
        if self.children.is_empty() {
            return None;
        }
        let mut sorted: Vec<&BookMoves> = self.children.values().collect();
        sorted.sort_by(|&a, &b| b.count.cmp(&a.count));
        let weights: Vec<u32> = sorted.iter().map(|v| v.count).collect();
        let moves: Vec<&String> = sorted.iter().map(|v| &v.move_str).collect();
        let wi = WeightedIndex::new(weights).unwrap();

        Some(&moves[wi.sample(&mut thread_rng())])
    }

    pub fn print_children(&self) {
        let mut sorted: Vec<(&String, &u32)> = self
            .children
            .values()
            .map(|kv| (&kv.move_str, &kv.count))
            .collect();
        sorted.sort_by(|&a, &b| b.1.cmp(a.1));
        for (mv, count) in sorted {
            println!("{mv}: {count}");
        }
    }
}
