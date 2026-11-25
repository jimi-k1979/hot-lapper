# `match` statements

`match` compares one value against a series of *patterns* and runs the first `case` that fits. It is more than a `switch`: patterns can check a value's type and pull out its parts in the same step.

```python
match frame:
    case TitleFrame(background=background, texts=texts):
        self._canvas.fill(background)
```

The kinds of pattern used so far:

- **Class patterns**, `TitleFrame(background=background)`: does the value pass `isinstance(frame, TitleFrame)`? If so, bind its `background` attribute to a local name. `Title()` with no arguments only checks the type.
- **Value patterns**, `case pygame.K_ESCAPE:`: a dotted name is compared with `==`. A bare name such as `case escape:` would instead *capture* anything into a new variable, which is why constants must be dotted.
- **Sequence patterns**, `case [TitleFrame(...)]`: matches a sequence of exactly that shape.
- **Wildcard**, `case _:`: matches anything.

## Why here

The screen flow and the renderer both branch on *which kind* of screen or frame they have. Today there is one kind, but `Screen` and `Frame` are unions that will grow. When a new member is added, mypy reports each `match` that no longer covers every case and so can fall off the end without returning. That makes it hard to forget a branch. The keyboard adapter uses `match` to turn key codes into commands.

## In the code

- [`application/screens.py`](../../src/hotlapper/application/screens.py): `transition` and `frame_for`
- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `present`
- [`adapters/pygame_keyboard.py`](../../src/hotlapper/adapters/pygame_keyboard.py): key codes and event types
