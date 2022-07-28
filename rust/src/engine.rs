use super::arrayboard::{ArrayBoard, BitMove};

const MAX_DEPTH: u8 = 3;

fn eval(board: ArrayBoard) -> i64 {
    0
}

pub fn search(
    board: ArrayBoard,
    mut alpha: i64,
    beta: i64,
    depth: u8,
) -> (Option<BitMove>, i64, u64) {
    if depth == MAX_DEPTH {
        return (None, eval(board), 1);
    }
    let moves = board.generate_moves();
    // Check for checkmate and stalemate.
    if moves.len() == 0 {
        return (None, 0, 1);
    }

    let mut nodes = 0;
    let mut best_move: Option<BitMove> = None;

    for mv in moves {
        let new_board = board.make_move(&mv);
        let (bm, score, child_nodes) = search(new_board, -beta, -alpha, depth + 1);
        nodes += child_nodes;

        if -score > beta {
            continue;
        }
        if -score > alpha {
            alpha = -score;
        }
    }
    (None, alpha, nodes)
}
