# `type` aliases

Python 3.12 added the `type` statement (PEP 695) for naming a type:

```python
type Seconds = float
type Frame = MenuFrame
type Rect = tuple[int, int, int, int]
```

An alias is not a new type. Any `float` is accepted where `Seconds` is expected. What it adds is meaning: `def now(self) -> Seconds` says more than `-> float`. It also gives one place to change if the underlying type ever changes. The right-hand side is evaluated lazily, so an alias can refer to classes defined further down the file.

## Why here

- `Seconds` documents the unit at every port and in the loop.
- `Screen` names the union of screen states (`Title | CircuitSelect | LapCount | CarSelect`). `Frame` has one member for now, because every menu draws with the same parts, and later tickets add more (`type Frame = MenuFrame | RaceFrame | ...`) without changing any signature that uses the alias.
- `Rect`, `Pixel` and `RGB` name tuple shapes that would otherwise be repeated.

## In the code

- [`application/ports.py`](../../src/hotlapper/application/ports.py): `Seconds`
- [`application/screens.py`](../../src/hotlapper/application/screens.py): `Screen`
- [`domain/frame.py`](../../src/hotlapper/domain/frame.py): `Frame` and `Pixel`
- [`domain/font.py`](../../src/hotlapper/domain/font.py): `Rect`
- [`domain/circuit.py`](../../src/hotlapper/domain/circuit.py): `Metres`, `Point` and the `Section` union
- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `RGB`
