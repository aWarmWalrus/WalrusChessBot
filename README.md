# Walrus Chess Bot

This repo is my way of learning about how chess engines work by implementing
them from scratch.

I implemented a basic alpha-beta bot in python and found that to be way too slow
(~500 nodes per second) even after using pseudo bitmaps.

In my second attempt, I implement the same basic chess engine in Rust. So far,
the speed-up has been just night and day (~2.4m nodes per second).
