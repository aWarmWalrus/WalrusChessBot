use crate::moves::BitMove;

pub trait ChessBoard {
    // Factory method
    fn create_from_fen(fen: &str) -> Self;

    // Generate pseudo legal moves in the sense that these moves may leave king in check.
    fn generate_moves(&self) -> Vec<BitMove>;
    fn make_move(&mut self, mv: &mut BitMove) -> Option<bool>;
    fn take_back_move(&mut self, mv: &BitMove);
    fn hash(&self) -> u64;

    fn get_piece(&self, index: usize) -> u32;
    fn white_to_move(&self) -> bool;

    fn is_king_checked(&self) -> bool;
    fn pretty_print(&self, verbose: bool);
}
