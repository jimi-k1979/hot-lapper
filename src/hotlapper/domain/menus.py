from collections.abc import Iterator, Sequence
from enum import Enum, auto
from typing import Final

from hotlapper.domain.canvas import CANVAS_WIDTH
from hotlapper.domain.car import CAR_ROSTER, Car, durability, pace
from hotlapper.domain.circuit import Circuit
from hotlapper.domain.font import ADVANCE, text_width
from hotlapper.domain.frame import Bar, Box, Line, MenuFrame, Pixel, Text
from hotlapper.domain.palette import Colour


class TitleItem(Enum):
    START = auto()
    RESET = auto()
    QUIT = auto()


class Answer(Enum):
    YES = auto()
    NO = auto()


TITLE_LABELS: Final = {
    TitleItem.START: "START",
    TitleItem.RESET: "RESET LAP RECORDS",
    TitleItem.QUIT: "QUIT",
}
CONTROLS: Final = (
    "A S D F  STEER",
    "I K      ACCELERATE  BRAKE",
    "J L      GEAR DOWN  UP",
    "ARROWS   MENUS",
    "ENTER    CHOOSE",
    "ESC      BACK",
    "F11      FULLSCREEN",
)
NO_LAP_RECORD: Final = "--:--.--"

CENTRE: Final = CANVAS_WIDTH // 2
SELECTED: Final = Colour.AMBER
UNSELECTED: Final = Colour.LIGHT_GREY

COLUMN_WIDTH: Final = 84
MAP_TOP: Final = 18
MAP_SIZE: Final = 64
MAP_INSET: Final = 10
CHEQUER: Final = 2

ROW_TOP: Final = 16
ROW_HEIGHT: Final = 58
DETAILS_X: Final = 88
BAR_X: Final = 154
BAR_WIDTH: Final = 90
BAR_HEIGHT: Final = 5
PICTURE_SCALE: Final = 2

CAR_PICTURE: Final = (
    "BBB.............................",
    "BBB.............WW..............",
    ".B.............WWWW.............",
    ".B......BBBBBBBKWWKBBBB.........",
    ".BBBBBBBBBBBBBBBBBBBBBBBBBBB....",
    "..KKKK..BBBBBBBBBBBBBBBB.KKK....",
    ".KKKKKK.BBBBBBBBBBBBBBB.KKKKK.BB",
    ".KKGGKK..BBBBBBBBBBBBB..KKGKKBBB",
    ".KKKKKK.................KKKKK...",
    "..KKKK...................KKK....",
)
PICTURE_COLOURS: Final = {"K": Colour.BLACK, "G": Colour.LIGHT_GREY, "W": Colour.WHITE}


def title_frame(item: TitleItem, reset: Answer | None) -> MenuFrame:
    texts = [_centred("HOT LAPPER", 16, Colour.AMBER, scale=3)]
    if reset is None:
        texts.extend(
            _centred(label, 56 + 12 * row, _highlight(choice is item))
            for row, (choice, label) in enumerate(TITLE_LABELS.items())
        )
    else:
        texts.append(_centred("RESET ALL LAP RECORDS?", 60, Colour.WHITE))
        texts.append(_centred("YES", 76, _highlight(reset is Answer.YES), CENTRE - 24))
        texts.append(_centred("NO", 76, _highlight(reset is Answer.NO), CENTRE + 24))
    texts.append(_centred("CONTROLS", 102, Colour.WHITE))
    texts.extend(
        Text(40, 116 + 10 * row, line, UNSELECTED) for row, line in enumerate(CONTROLS)
    )
    return MenuFrame(background=Colour.BLACK, texts=tuple(texts))


def circuit_select_frame(
    circuits: Sequence[Circuit], selected: int, laps: int | None = None
) -> MenuFrame:
    texts = [_centred("CHOOSE A CIRCUIT", 4, Colour.WHITE)]
    boxes: list[Box] = []
    lines: list[Line] = []
    left = (CANVAS_WIDTH - len(circuits) * COLUMN_WIDTH) // 2
    for index, circuit in enumerate(circuits):
        x = left + index * COLUMN_WIDTH
        centre = x + COLUMN_WIDTH // 2
        points = [
            (x + MAP_INSET + round(u * MAP_SIZE), MAP_TOP + round(v * MAP_SIZE))
            for u, v in circuit.outline
        ]
        lines.extend(
            Line(start, end, Colour.WHITE)
            for start, end in zip(points, points[1:] + points[:1], strict=True)
        )
        boxes.extend(_chequer(points[0]))
        if index == selected:
            boxes.extend(_outline(x + 2, 14, COLUMN_WIDTH - 4, 108, SELECTED))
        name_lines = _wrap(circuit.name.upper(), (COLUMN_WIDTH - 8) // ADVANCE)
        texts.extend(
            _centred(line, 88 + 9 * row, _highlight(index == selected), centre)
            for row, line in enumerate(name_lines)
        )
        texts.append(_centred(NO_LAP_RECORD, 110, Colour.WHITE, centre))
    if laps is not None:
        texts.append(_centred(f"LAPS  < {laps} >", 150, SELECTED))
    return MenuFrame(
        background=Colour.BLACK,
        texts=tuple(texts),
        boxes=tuple(boxes),
        lines=tuple(lines),
    )


def car_select_frame(selected: int) -> MenuFrame:
    texts = [_centred("CHOOSE A CAR", 4, Colour.WHITE)]
    boxes: list[Box] = []
    bars: list[Bar] = []
    for index, car in enumerate(CAR_ROSTER):
        y = ROW_TOP + index * ROW_HEIGHT
        if index == selected:
            boxes.extend(_outline(2, y, CANVAS_WIDTH - 4, ROW_HEIGHT - 2, SELECTED))
        boxes.append(Box(6, y + 6, 76, 30, Colour.DARK_GREEN))
        boxes.extend(_picture(car, 12, y + 11))
        texts += [
            Text(DETAILS_X, y + 5, car.name, _highlight(index == selected)),
            Text(DETAILS_X, y + 14, car.transmission.upper(), UNSELECTED),
            Text(DETAILS_X, y + 24, "PACE", UNSELECTED),
            Text(DETAILS_X, y + 33, "DURABILITY", UNSELECTED),
            Text(8, y + 45, car.description, UNSELECTED),
        ]
        bars += [
            Bar(BAR_X, y + 25, BAR_WIDTH, BAR_HEIGHT, pace(car), Colour.AMBER),
            Bar(
                BAR_X,
                y + 34,
                BAR_WIDTH,
                BAR_HEIGHT,
                durability(car),
                Colour.LIGHT_GREEN,
            ),
        ]
    return MenuFrame(
        background=Colour.BLACK,
        texts=tuple(texts),
        boxes=tuple(boxes),
        bars=tuple(bars),
    )


def _highlight(selected: bool) -> Colour:
    return SELECTED if selected else UNSELECTED


def _centred(
    string: str, y: int, colour: Colour, centre: int = CENTRE, scale: int = 1
) -> Text:
    return Text(centre - text_width(string, scale) // 2, y, string, colour, scale)


def _wrap(string: str, width: int) -> list[str]:
    lines: list[str] = []
    for word in string.split():
        if lines and len(lines[-1]) + 1 + len(word) <= width:
            lines[-1] += f" {word}"
        else:
            lines.append(word)
    return lines


def _outline(x: int, y: int, width: int, height: int, colour: Colour) -> list[Box]:
    return [
        Box(x, y, width, 1, colour),
        Box(x, y + height - 1, width, 1, colour),
        Box(x, y, 1, height, colour),
        Box(x + width - 1, y, 1, height, colour),
    ]


def _chequer(at: Pixel) -> Iterator[Box]:
    x, y = at
    left, top = x - 2 * CHEQUER - 1, y - CHEQUER - 1
    yield Box(left, top, 4 * CHEQUER + 2, 2 * CHEQUER + 2, Colour.WHITE)
    for row in range(2):
        for column in range(row % 2, 4, 2):
            yield Box(
                left + 1 + column * CHEQUER,
                top + 1 + row * CHEQUER,
                CHEQUER,
                CHEQUER,
                Colour.BLACK,
            )


def _picture(car: Car, x: int, y: int) -> Iterator[Box]:
    colours = {**PICTURE_COLOURS, "B": car.colour}
    for row, pixels in enumerate(CAR_PICTURE):
        for column, pixel in enumerate(pixels):
            if pixel in colours:
                yield Box(
                    x + column * PICTURE_SCALE,
                    y + row * PICTURE_SCALE,
                    PICTURE_SCALE,
                    PICTURE_SCALE,
                    colours[pixel],
                )
