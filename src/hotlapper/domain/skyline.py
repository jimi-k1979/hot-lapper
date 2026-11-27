import math
from collections.abc import Iterator, Mapping
from typing import Final

type Shape = Iterator[tuple[int, int]]

SKYLINE_WIDTH: Final = 804
GROUND: Final = 2


def _block(x: int, width: int, height: int) -> Shape:
    for column in range(x, x + width):
        yield column, height


def _mound(x: int, width: int, height: int) -> Shape:
    radius = width / 2
    for column in range(width):
        across = (column + 0.5 - radius) / radius
        yield x + column, round(height * math.sqrt(1 - across * across))


def _skyline(*shapes: Shape) -> tuple[int, ...]:
    heights = [GROUND] * SKYLINE_WIDTH
    for shape in shapes:
        for column, height in shape:
            x = column % SKYLINE_WIDTH
            heights[x] = max(heights[x], height)
    return tuple(heights)


AIRFIELD: Final = _skyline(
    _mound(0, 40, 8),
    _mound(28, 34, 11),
    _mound(56, 50, 7),
    _block(150, 70, 6),
    _mound(150, 70, 12),
    _block(226, 70, 6),
    _mound(226, 70, 12),
    _block(330, 8, 16),
    _block(333, 2, 24),
    _block(345, 40, 5),
    _mound(420, 26, 9),
    _mound(440, 40, 12),
    _mound(474, 30, 8),
    _mound(500, 60, 10),
    _block(610, 30, 7),
    _block(616, 18, 9),
    _mound(680, 44, 9),
    _mound(716, 36, 13),
    _mound(748, 60, 8),
)

SKYLINES: Final[Mapping[str, tuple[int, ...]]] = {"airfield": AIRFIELD}
