# `match` statements

`match` compares one value against a series of *patterns* and runs the first `case` that fits. It is more than a `switch`: patterns can check a value's type and pull out its parts in the same step.

```python
match frame:
    case MenuFrame(background=background, texts=texts):
        self._canvas.fill(background)
```

The kinds of pattern used so far:

- **Class patterns**, `MenuFrame(background=background)`: does the value pass `isinstance(frame, MenuFrame)`? If so, bind its `background` attribute to a local name. `CarSelect()` with no arguments only checks the type, and `Title(reset=None)` checks an attribute's value too.
- **Value patterns**, `case pygame.K_ESCAPE:`: a dotted name is compared with `==`. A bare name such as `case escape:` would instead *capture* anything into a new variable, which is why constants must be dotted.
- **Wildcard**, `case _:`: matches anything. After every member of a union has been matched, `case _: assert_never(frame)` asks mypy to prove that the wildcard can never be reached.
- **Keyword captures**, `Corner(turn=turn, radius=radius)`: pull several attributes out at once.
- **Guards**, `case Corner(radius=radius) if radius < ARROW_RADIUS:`: the case matches only if the pattern fits *and* the condition is true.
- **Enum members**, `case _SectionKind.STRAIGHT:`: a dotted value pattern. mypy knows when every member has been covered, just as it does for a union.
- **Or-patterns**, `case Command.UP | Command.DOWN:`: the case matches if any of the alternatives does.
- **Sequence patterns**, `match command, title.item:` then `case Command.CONFIRM, TitleItem.QUIT:`: matching a tuple lets one `case` depend on two values at once. Each position takes its own pattern, so `case (Command.BACK, _):` ignores the second.

## Why here

The screen flow and the renderer both branch on *which kind* of screen or frame they have. `Screen` has a member per menu, and `Frame` is a union that will grow. When a new member is added, mypy reports each `match` that no longer covers it. In `transition` and `frame_for`, an unhandled case would fall off the end without returning a value, which is an error. `present` returns nothing, so it ends with `assert_never` instead. Either way, it is hard to forget a branch. The keyboard adapter uses `match` to turn key codes into commands. In the Title menu, matching the command and the highlighted item together reads like a table of what each key does on each item.

## In the code

- [`application/screens.py`](../../src/hotlapper/application/screens.py): `transition` and `frame_for`
- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `present`
- [`adapters/pygame_keyboard.py`](../../src/hotlapper/adapters/pygame_keyboard.py): key codes and event types
- [`domain/circuit.py`](../../src/hotlapper/domain/circuit.py): `_curvature` and `_corner_arrows` over the `Section` union
- [`adapters/circuit_loader.py`](../../src/hotlapper/adapters/circuit_loader.py): `_section` over the section kinds
