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
class Bar:
    x: int
    y: int
    width: int
    height: int
    fraction: float
    colour: Colour


@dataclass(frozen=True, slots=True)
class MenuFrame:
    background: Colour
    texts: tuple[Text, ...]
    boxes: tuple[Box, ...] = ()
    lines: tuple[Line, ...] = ()
    bars: tuple[Bar, ...] = ()


type Frame = MenuFrame
