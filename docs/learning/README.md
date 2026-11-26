# Learning notes

Short explainers for the Python features Hot Lapper uses. Each one is written in the pull request that first uses the feature, and links to the code that uses it.

## Explainers

- [Protocols](protocols.md): the ports the core talks through
- [Frozen, slotted dataclasses](dataclasses.md): immutable value types such as `Controls` and `Frame`
- [`match` statements](match.md): branching on screens, frames and keys
- [`type` aliases](type-aliases.md): naming `Seconds`, `Frame` and `Screen`
- [Constructor injection](constructor-injection.md): wiring the game in one composition root
- [Context managers](context-managers.md): the pygame display's lifecycle, and `Self`
- [Enums](enums.md): commands, palette colours and the words in circuit files
- [`Final`](final.md): constants mypy won't let you reassign
- [Generic functions](generics.md): one typed `choice` for every enum a circuit file uses
- [Exception chaining](exception-chaining.md): `raise ... from`, and naming the circuit file in a `CircuitDataError`
- [Hypothesis](hypothesis.md): property tests for segment lookup round the loop
- [Generators](generators.md): the font yielding pixel rectangles
