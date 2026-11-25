# `Final`

`typing.Final` marks a name that must never be reassigned:

```python
CANVAS_WIDTH: Final = 256
STEP: Final[Seconds] = 1 / 60
```

mypy reports any later `CANVAS_WIDTH = ...` as an error. Python itself doesn't enforce this at run time. With a bare `Final`, mypy infers the type from the value, and the value is known exactly (`256`, not just some `int`).

`Final` stops the *name* being rebound. It doesn't make the value immutable. That is why the palette and glyph tables are annotated with `Mapping`, which has no methods for changing it.

## Why here

The canvas size, the step length, the catch-up cap and the palette are tuning constants (ADR 0001 makes the canvas and palette core constants). Marking them `Final` means mypy catches any accidental reassignment.

## In the code

- [`domain/canvas.py`](../../src/hotlapper/domain/canvas.py)
- [`application/loop.py`](../../src/hotlapper/application/loop.py): `STEP` and `MAX_STEPS_PER_TICK`
- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `EARTHY`
