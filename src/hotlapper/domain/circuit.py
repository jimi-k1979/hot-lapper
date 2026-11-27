import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Final

from hotlapper.domain.skyline import SKYLINES

type CircuitId = str
type Metres = float
type Point = tuple[float, float]

SEGMENT_LENGTH: Final = 5
BAND_SEGMENTS: Final = 3
GRID_ROWS: Final = 5
GRID_FRONT_GAP: Final = 5
GRID_ROW_SPACING: Final = 16
GRID_STAGGER: Final = 8
GRID_BOX_LENGTH: Final = 5
OUTER_LIMIT: Final = 6
ARROW_RADIUS: Final = 200
ARROW_APPROACH: Final = 150
ARROW_BOARDS: Final = 3
ARROW_SETBACK: Final = 2
MAX_GRADIENT: Final = 0.1


class CircuitDataError(Exception):
    def __init__(self, field: str, problem: str, file: str | None = None) -> None:
        where = f"{file}: " if file else ""
        super().__init__(f"{where}{field}: {problem}")
        self.field = field
        self.problem = problem
        self.file = file

    def in_file(self, file: str) -> "CircuitDataError":
        return CircuitDataError(self.field, self.problem, file)


class Side(StrEnum):
    LEFT = auto()
    RIGHT = auto()

    @property
    def sign(self) -> int:
        return -1 if self is Side.LEFT else 1


class HazardKind(StrEnum):
    OIL = auto()
    WATER = auto()
    GLASS = auto()
    DEBRIS = auto()
    ROCKS = auto()


class SceneryKind(StrEnum):
    TREE = auto()
    BUSH = auto()
    BARN = auto()
    GRANDSTAND = auto()
    MARKER_POST = auto()


@dataclass(frozen=True, slots=True)
class Straight:
    length: Metres
    climb: Metres = 0


@dataclass(frozen=True, slots=True)
class Corner:
    turn: Side
    radius: Metres
    enter: Metres
    hold: Metres
    leave: Metres
    climb: Metres = 0

    @property
    def length(self) -> Metres:
        return self.enter + self.hold + self.leave


type Section = Straight | Corner


@dataclass(frozen=True, slots=True)
class Hazard:
    kind: HazardKind
    at: Metres
    across: Metres
    length: Metres
    width: Metres


@dataclass(frozen=True, slots=True)
class Scenery:
    kind: SceneryKind
    at: Metres
    across: Metres


@dataclass(frozen=True, slots=True)
class PitArea:
    side: Side
    at: Metres
    length: Metres


@dataclass(frozen=True, slots=True)
class CornerArrow:
    at: Metres
    across: Metres
    turn: Side


@dataclass(frozen=True, slots=True)
class GridBox:
    at: Metres
    across: Metres


@dataclass(frozen=True, slots=True)
class Segment:
    start: Metres
    curve: float
    height: Metres
    end_height: Metres
    light_band: bool


@dataclass(frozen=True, slots=True)
class Circuit:
    circuit_id: CircuitId
    name: str
    order: int
    width: Metres
    skyline: str
    segments: tuple[Segment, ...]
    hazards: tuple[Hazard, ...]
    scenery: tuple[Scenery, ...]
    corner_arrows: tuple[CornerArrow, ...]
    grid: tuple[GridBox, ...]
    pit_area: PitArea
    outline: tuple[Point, ...]

    @property
    def length(self) -> Metres:
        return len(self.segments) * SEGMENT_LENGTH

    def segment_at(self, distance: Metres) -> Segment:
        index = int(distance // SEGMENT_LENGTH)
        return self.segments[index % len(self.segments)]


def build_circuit(
    *,
    circuit_id: CircuitId,
    name: str,
    order: int,
    width: Metres,
    skyline: str,
    sections: Sequence[Section],
    hazards: Sequence[Hazard],
    scenery: Sequence[Scenery],
    pit_area: PitArea,
    outline: Sequence[Point],
) -> Circuit:
    if skyline not in SKYLINES:
        raise CircuitDataError("skyline", f"should be one of {', '.join(SKYLINES)}")
    segments = _segments(sections)
    length = len(segments) * SEGMENT_LENGTH
    grid = _grid(length, width, pit_area.side)
    _check_pit_area(pit_area, length)
    _check_hazards(
        hazards,
        width,
        grid_start=grid[-1].at - GRID_BOX_LENGTH,
        pit_area=pit_area,
        length=length,
    )
    _check_scenery(scenery, width, length)
    _check_outline(outline)
    return Circuit(
        circuit_id=circuit_id,
        name=name,
        order=order,
        width=width,
        skyline=skyline,
        segments=segments,
        hazards=tuple(hazards),
        scenery=tuple(scenery),
        corner_arrows=_corner_arrows(sections, length, width),
        grid=grid,
        pit_area=pit_area,
        outline=tuple(outline),
    )


def _segments(sections: Sequence[Section]) -> tuple[Segment, ...]:
    if not sections:
        raise CircuitDataError("sections", "should not be empty")
    segments: list[Segment] = []
    base: Metres = 0
    for index, section in enumerate(sections):
        if isinstance(section, Corner) and section.radius <= 0:
            raise CircuitDataError(f"sections[{index}].radius", "should be positive")
        for step in range(int(section.length // SEGMENT_LENGTH)):
            near = step * SEGMENT_LENGTH
            far = near + SEGMENT_LENGTH
            number = len(segments)
            segment = Segment(
                start=number * SEGMENT_LENGTH,
                curve=_curvature(section, (near + far) / 2),
                height=base + _eased_climb(section, near),
                end_height=base + _eased_climb(section, far),
                light_band=number // BAND_SEGMENTS % 2 == 0,
            )
            if abs(segment.end_height - segment.height) > MAX_GRADIENT * SEGMENT_LENGTH:
                raise CircuitDataError(
                    f"sections[{index}].climb", "is steeper than the gradient cap"
                )
            segments.append(segment)
        base += section.climb
    if not math.isclose(base, 0, abs_tol=1e-9):
        raise CircuitDataError("sections", "climbs should sum to zero")
    return tuple(segments)


def _check_pit_area(pit_area: PitArea, length: Metres) -> None:
    if pit_area.length <= 0:
        raise CircuitDataError("pit_area.length", "should be positive")
    if pit_area.at < 0:
        raise CircuitDataError("pit_area.at", "is before the start/finish line")
    if pit_area.at + pit_area.length > length:
        raise CircuitDataError("pit_area.length", "runs past the end of the circuit")


def _check_hazards(
    hazards: Sequence[Hazard],
    width: Metres,
    *,
    grid_start: Metres,
    pit_area: PitArea,
    length: Metres,
) -> None:
    pit_end = pit_area.at + pit_area.length
    for index, hazard in enumerate(hazards):
        field = f"hazards[{index}]"
        end = hazard.at + hazard.length
        if hazard.length <= 0:
            raise CircuitDataError(f"{field}.length", "should be positive")
        if hazard.width <= 0:
            raise CircuitDataError(f"{field}.width", "should be positive")
        if abs(hazard.across) + hazard.width / 2 > width / 2:
            raise CircuitDataError(f"{field}.across", "is not wholly on the road")
        if hazard.at < 0 or end > length:
            raise CircuitDataError(f"{field}.at", "is not inside the circuit")
        if end > grid_start:
            raise CircuitDataError(f"{field}.at", "overlaps the grid")
        if hazard.at < pit_end and pit_area.at < end:
            raise CircuitDataError(f"{field}.at", "overlaps the pit area")


def _check_scenery(scenery: Sequence[Scenery], width: Metres, length: Metres) -> None:
    for index, item in enumerate(scenery):
        field = f"scenery[{index}]"
        if abs(item.across) <= width / 2 + OUTER_LIMIT:
            raise CircuitDataError(f"{field}.across", "is not beyond the outer limit")
        if not 0 <= item.at < length:
            raise CircuitDataError(f"{field}.at", "is not inside the circuit")


def _check_outline(outline: Sequence[Point]) -> None:
    if len(outline) < 3:
        raise CircuitDataError("outline", "should have at least 3 points")
    for index, (x, y) in enumerate(outline):
        if not (0 <= x <= 1 and 0 <= y <= 1):
            raise CircuitDataError(f"outline[{index}]", "is outside the unit square")


def _corner_arrows(
    sections: Sequence[Section], length: Metres, width: Metres
) -> tuple[CornerArrow, ...]:
    spacing = ARROW_APPROACH / ARROW_BOARDS
    arrows: list[CornerArrow] = []
    start: Metres = 0
    for section in sections:
        match section:
            case Corner(turn=turn, radius=radius) if radius < ARROW_RADIUS:
                across = -turn.sign * (width / 2 + OUTER_LIMIT + ARROW_SETBACK)
                arrows.extend(
                    CornerArrow(
                        at=(start - ARROW_APPROACH + board * spacing) % length,
                        across=across,
                        turn=turn,
                    )
                    for board in range(ARROW_BOARDS)
                )
        start += section.length
    return tuple(arrows)


def _grid(length: Metres, width: Metres, pit_side: Side) -> tuple[GridBox, ...]:
    pole_across = -pit_side.sign * width / 4
    boxes: list[GridBox] = []
    for row in range(GRID_ROWS):
        front = length - GRID_FRONT_GAP - row * GRID_ROW_SPACING
        boxes.append(GridBox(at=front, across=pole_across))
        boxes.append(GridBox(at=front - GRID_STAGGER, across=-pole_across))
    return tuple(boxes)


def _curvature(section: Section, distance: Metres) -> float:
    match section:
        case Straight():
            return 0
        case Corner(turn=turn, radius=radius, enter=enter, hold=hold, leave=leave):
            full = turn.sign / radius
            if distance < enter:
                return full * distance / enter
            if distance < enter + hold:
                return full
            return full * (enter + hold + leave - distance) / leave


def _eased_climb(section: Section, distance: Metres) -> Metres:
    t = distance / section.length
    return section.climb * t * t * (3 - 2 * t)
