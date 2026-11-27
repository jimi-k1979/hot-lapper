from dataclasses import dataclass

from hotlapper.domain.palette import Colour

type Pixel = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Text:
    x: int
    y: int
    string: str
    colour: Colour
    scale: int = 1


@dataclass(frozen=True, slots=True)
class Box:
    x: int
    y: int
    width: int
    height: int
    colour: Colour


@dataclass(frozen=True, slots=True)
class Line:
    start: Pixel
    end: Pixel
    colour: Colour


@dataclass(frozen=True, slots=True)
class MenuFrame:
    background: Colour
    texts: tuple[Text, ...]
    boxes: tuple[Box, ...] = ()
    lines: tuple[Line, ...] = ()


@dataclass(frozen=True, slots=True)
class Polygon:
    points: tuple[Pixel, ...]
    colour: Colour


@dataclass(frozen=True, slots=True)
class RaceFrame:
    boxes: tuple[Box, ...]
    polygons: tuple[Polygon, ...]


type Frame = MenuFrame | RaceFrame
