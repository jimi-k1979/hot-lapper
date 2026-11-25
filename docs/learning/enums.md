# Enums

An `Enum` is a fixed set of named values. Members are singletons, compared with `is` or `==`, and a misspelt member is an `AttributeError` instead of a silent bug.

```python
class Command(Enum):
    BACK = auto()
    FULLSCREEN = auto()
    QUIT = auto()
```

`auto()` picks the values for you. They don't matter, only the names do.

`IntEnum` members are also real `int`s:

```python
class Colour(IntEnum):
    BLACK = 0
    WHITE = 1
```

## Why here

- `Command` is the set of edge commands the keyboard can report. Strings would allow typos, and bare ints would be meaningless.
- `Colour` is the palette, and here the values *do* matter: each is the index into the 16-colour palette of the 8-bit canvas. Because `Colour.AMBER` is an `int`, pygame can fill with it directly, while the core still reads it by name. Iterating `for colour in Colour` goes in definition order, which here is also index order. That is how the display adapter builds the palette list.

## In the code

- [`domain/controls.py`](../../src/hotlapper/domain/controls.py): `Command`
- [`domain/palette.py`](../../src/hotlapper/domain/palette.py): `Colour`
- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `EARTHY` and `set_palette`
