# Generators

A function containing `yield` is a *generator function*. Calling it runs none of its body. Instead it returns an iterator, and each `next()` runs the body up to the next `yield` and hands back that value.

```python
def glyph_rects(string: str, x: int, y: int, scale: int = 1) -> Iterator[Rect]:
    for index, char in enumerate(string):
        ...
                if bit == "#":
                    yield (left + column * scale, y + row * scale, scale, scale)
```

The caller just loops over it:

```python
for rect in glyph_rects(text.string, text.x, text.y, text.scale):
    canvas.fill(text.colour, rect)
```

## Why here

Turning text into lit pixels is font knowledge, so it belongs in the domain (ADR 0001). Drawing them belongs to the adapter. A generator splits the work cleanly: the domain produces rectangles one at a time, and the adapter fills each one as it arrives, without a list of every pixel being built first. The return type is `Iterator[Rect]` from `collections.abc`.

## Handing on another iterator: `yield from`

`yield from iterator` yields every item of another iterator in turn. `visible_segments` builds its iterator from `itertools` pieces (see [itertools](itertools.md)) and hands it on this way.

Generators also chain. `_spans` loops over `visible_segments`, works out each segment's sideways bend, and yields one span at a time, so the road is built strip by strip without a list of segments in between.

## In the code

- [`domain/font.py`](../../src/hotlapper/domain/font.py): `glyph_rects`
- [`domain/menus.py`](../../src/hotlapper/domain/menus.py): `_chequer` and `_picture`, yielding boxes
- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `present`
- [`domain/road.py`](../../src/hotlapper/domain/road.py): `visible_segments`, `_spans` and `_paintwork`
- [`domain/skyline.py`](../../src/hotlapper/domain/skyline.py): `_block` and `_mound`, yielding skyline columns
