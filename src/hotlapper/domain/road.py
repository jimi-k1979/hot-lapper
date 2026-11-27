import math
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import count, cycle, islice
from typing import Final

from hotlapper.domain.canvas import CANVAS_HEIGHT, CANVAS_WIDTH
from hotlapper.domain.circuit import (
    GRID_BOX_LENGTH,
    SEGMENT_LENGTH,
    Circuit,
    Metres,
    Segment,
)
from hotlapper.domain.frame import Polygon
from hotlapper.domain.palette import Colour

FIELD_OF_VIEW: Final = math.radians(90)
HORIZON: Final = 82
DRAW_DISTANCE: Final = 80
FOCAL_LENGTH: Final = CANVAS_WIDTH / 2 / math.tan(FIELD_OF_VIEW / 2)
EYE_HEIGHT: Final = 1.0
NEAR_PLANE: Final = 0.5
KERB_WIDTH: Final = 0.8
CHEQUERS: Final = 8
PAINT_WIDTH: Final = 0.25
GRID_MARGIN: Final = 0.6
PIT_DASH: Final = 2.5
HATCH_SPACING: Final = 5.0
HATCH_RUN: Final = 4.0
HATCH_WIDTH: Final = 0.8
HATCH_MARGIN: Final = 0.4

LIGHT_SHADES: Final = (Colour.LIGHT_GREEN, Colour.RED, Colour.MID_GREY)
DARK_SHADES: Final = (Colour.DARK_GREEN, Colour.WHITE, Colour.DARK_GREY)


@dataclass(frozen=True, slots=True)
class Camera:
    across: Metres
    height: Metres


@dataclass(frozen=True, slots=True)
class CrossSection:
    y: float
    centre: float
    scale: float

    def x(self, across: Metres) -> float:
        return self.centre + across * self.scale


@dataclass(frozen=True, slots=True)
class _Span:
    ahead: Metres
    sideways: Metres
    end_sideways: Metres
    height: Metres
    end_height: Metres

    def at(self, along: float, camera: Camera) -> CrossSection:
        return project(
            camera,
            self.ahead + along * SEGMENT_LENGTH,
            _between(self.sideways, self.end_sideways, along),
            _between(self.height, self.end_height, along),
        )


@dataclass(frozen=True, slots=True)
class _Paint:
    at: Metres
    length: Metres
    across: Metres
    width: Metres
    colour: Colour
    lean: float = 0


def project(
    camera: Camera, ahead: Metres, sideways: Metres, height: Metres
) -> CrossSection:
    scale = FOCAL_LENGTH / ahead
    return CrossSection(
        y=HORIZON + (camera.height - height) * scale,
        centre=CANVAS_WIDTH / 2 + (sideways - camera.across) * scale,
        scale=scale,
    )


def visible_segments(
    circuit: Circuit, distance: Metres
) -> Iterator[tuple[Metres, Segment]]:
    first = int(distance // SEGMENT_LENGTH)
    behind = distance - first * SEGMENT_LENGTH
    start = first % len(circuit.segments)
    ahead = count(-behind, SEGMENT_LENGTH)
    segments = islice(cycle(circuit.segments), start, start + DRAW_DISTANCE)
    yield from zip(ahead, segments, strict=False)


def road_height(circuit: Circuit, distance: Metres) -> Metres:
    segment = circuit.segment_at(distance)
    along = (distance % circuit.length - segment.start) / SEGMENT_LENGTH
    return _between(segment.height, segment.end_height, along)


def road_polygons(circuit: Circuit, distance: Metres, lateral: Metres) -> list[Polygon]:
    camera = Camera(lateral, road_height(circuit, distance) + EYE_HEIGHT)
    paintwork = _paintwork_by_segment(circuit)
    polygons: list[Polygon] = []
    bottom = float(CANVAS_HEIGHT)
    unfinished: CrossSection | None = None
    for span, segment in _spans(circuit, distance):
        nearest = max(0.0, (NEAR_PLANE - span.ahead) / SEGMENT_LENGTH)
        if nearest >= 1:
            continue
        near, far = span.at(nearest, camera), span.at(1, camera)
        if far.y >= bottom:
            unfinished = None
            continue
        if unfinished is not None:
            near = unfinished
        if _within_a_row(near, far, bottom):
            unfinished = near
            continue
        if _side_on(near, far, circuit.width / 2):
            break
        unfinished = None
        polygons += _surface(near, far, bottom, circuit.width, segment.light_band)
        for paint in paintwork.get(segment.start, ()):
            mark = _mark(paint, span, camera, nearest, bottom)
            if mark is not None:
                polygons.append(mark)
        bottom = far.y
    return polygons


def _mark(
    paint: _Paint, span: _Span, camera: Camera, nearest: float, bottom: float
) -> Polygon | None:
    start = max(paint.at / SEGMENT_LENGTH, nearest)
    end = (paint.at + paint.length) / SEGMENT_LENGTH
    if end <= start:
        return None
    near, far = span.at(start, camera), span.at(end, camera)
    if far.y >= bottom or _within_a_row(near, far, bottom):
        return None
    across = paint.across + paint.lean * (start * SEGMENT_LENGTH - paint.at)
    shift = paint.lean * (end - start) * SEGMENT_LENGTH
    half = paint.width / 2
    return _quad(near, far, across - half, across + half, paint.colour, bottom, shift)


def _spans(circuit: Circuit, distance: Metres) -> Iterator[tuple[_Span, Segment]]:
    sideways = drift = 0.0
    for ahead, segment in visible_segments(circuit, distance):
        if ahead <= 0:
            # Turn relative to the car's own heading, so the road never jumps
            # as the car crosses a segment boundary.
            sideways, drift = segment.curve * ahead**2 / 2, segment.curve * ahead
        turn = segment.curve * SEGMENT_LENGTH
        end_sideways = sideways + (drift + turn / 2) * SEGMENT_LENGTH
        yield (
            _Span(ahead, sideways, end_sideways, segment.height, segment.end_height),
            segment,
        )
        sideways, drift = end_sideways, drift + turn


def _side_on(near: CrossSection, far: CrossSection, half: Metres) -> bool:
    gap = (far.x(half) - far.x(-half)) * (near.y - far.y)
    rightwards = far.x(half) - near.x(half)
    leftwards = near.x(-half) - far.x(-half)
    return rightwards > gap or leftwards > gap


def _within_a_row(near: CrossSection, far: CrossSection, bottom: float) -> bool:
    return round(min(near.y, bottom)) == round(far.y)


def _surface(
    near: CrossSection, far: CrossSection, bottom: float, width: Metres, light: bool
) -> list[Polygon]:
    grass, kerb, road = LIGHT_SHADES if light else DARK_SHADES
    half = width / 2
    top, base = round(far.y), round(min(near.y, bottom))
    return [
        Polygon(
            ((0, base), (CANVAS_WIDTH, base), (CANVAS_WIDTH, top), (0, top)), grass
        ),
        _quad(near, far, -half - KERB_WIDTH, half + KERB_WIDTH, kerb, bottom),
        _quad(near, far, -half, half, road, bottom),
    ]


def _quad(
    near: CrossSection,
    far: CrossSection,
    left: Metres,
    right: Metres,
    colour: Colour,
    bottom: float,
    shift: Metres = 0,
) -> Polygon:
    far_left, far_right = far.x(left + shift), far.x(right + shift)
    near_left, near_right, near_y = near.x(left), near.x(right), near.y
    if near_y > bottom:
        along = (near_y - bottom) / (near_y - far.y)
        near_left = _between(near_left, far_left, along)
        near_right = _between(near_right, far_right, along)
        near_y = bottom
    points = (
        (near_left, near_y),
        (near_right, near_y),
        (far_right, far.y),
        (far_left, far.y),
    )
    return Polygon(tuple((round(x), round(y)) for x, y in points), colour)


def _paintwork_by_segment(circuit: Circuit) -> Mapping[Metres, Sequence[_Paint]]:
    pieces: defaultdict[Metres, list[_Paint]] = defaultdict(list)
    for paint in _paintwork(circuit):
        end = paint.at + paint.length
        first = int(paint.at // SEGMENT_LENGTH)
        last = math.ceil(end / SEGMENT_LENGTH)
        for number in range(first, last):
            start = number * SEGMENT_LENGTH
            near, far = max(paint.at, start), min(end, start + SEGMENT_LENGTH)
            if far > near:
                segment = circuit.segment_at(start)
                across = paint.across + paint.lean * (near - paint.at)
                pieces[segment.start].append(
                    replace(paint, at=near - start, length=far - near, across=across)
                )
    return pieces


def _paintwork(circuit: Circuit) -> Iterator[_Paint]:
    square = circuit.width / CHEQUERS
    for row in range(2):
        for column in range(CHEQUERS):
            yield _Paint(
                at=row * square,
                length=square,
                across=(column + 0.5) * square - circuit.width / 2,
                width=square,
                colour=Colour.BLACK if (row + column) % 2 else Colour.WHITE,
            )
    box_width = circuit.width / 2 - 2 * GRID_MARGIN
    for box in circuit.grid:
        yield _Paint(
            box.at - PAINT_WIDTH, PAINT_WIDTH, box.across, box_width, Colour.WHITE
        )
        for side in (-1, 1):
            yield _Paint(
                at=box.at - GRID_BOX_LENGTH,
                length=GRID_BOX_LENGTH,
                across=box.across + side * box_width / 2,
                width=PAINT_WIDTH,
                colour=Colour.WHITE,
            )
    pit_area = circuit.pit_area
    for dash in range(int(pit_area.length // (2 * PIT_DASH))):
        yield _Paint(
            at=pit_area.at + dash * 2 * PIT_DASH,
            length=PIT_DASH,
            across=0,
            width=PAINT_WIDTH,
            colour=Colour.AMBER,
        )
    side = pit_area.side.sign
    start = HATCH_MARGIN + HATCH_WIDTH / 2
    span = circuit.width / 2 - 2 * start
    for hatch in range(int((pit_area.length - HATCH_RUN) // HATCH_SPACING) + 1):
        yield _Paint(
            at=pit_area.at + hatch * HATCH_SPACING,
            length=HATCH_RUN,
            across=side * start,
            width=HATCH_WIDTH,
            colour=Colour.AMBER,
            lean=side * span / HATCH_RUN,
        )


def _between(start: float, end: float, along: float) -> float:
    return start * (1 - along) + end * along
