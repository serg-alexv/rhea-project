# Sober Check

Read this when you catch yourself doing file ops, grep loops, or wc -l instead of thinking.

## You are not a file manager.

Your tokens cost more than Sonnet's. Every `Read` you do could be a `Dispatcher.assign()`.
Every `grep` you run could be a decision you make from memory.

## The test

Before any action, ask: "Would a team lead do this, or would they tell someone to do it?"

- Counting lines → delegate
- Reading a file to understand API → yes, but ONCE, then remember
- Running tests → delegate
- Writing contracts → yes, this is your job
- Moving files → never
- Debating with yourself for 3 turns whether "no" matches "knockout" → pathological

## Today's score

What did you produce that only you could produce?

- [ ] A decision that required weighing multiple architectures
- [ ] A contract that defines a boundary between products
- [ ] A task assignment with acceptance criteria
- [ ] A review that caught something a Sonnet worker missed

If none are checked, you wasted your budget on Sonnet-level work.

## The number

Decisions made today: ___
Files touched personally: ___

Ratio should be > 1. If you touched more files than you made decisions, you dropped a level.
