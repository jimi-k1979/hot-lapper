from itertools import groupby
from operator import itemgetter
from typing import Final

from hotlapper.domain.canvas import CANVAS_HEIGHT, CANVAS_WIDTH
from hotlapper.domain.circuit import Circuit
from hotlapper.domain.frame import Box, RaceFrame
from hotlapper.domain.palette import Colour
from hotlapper.domain.race import Race
from hotlapper.domain.road import (
    EYE_HEIGHT,
    FOCAL_LENGTH,
    HORIZON,
    road_height,
    road_polygons,
)
from hotlapper.domain.skyline import SKYLINES

PALE_BAND: Final = 8
SKYLINE_DISTANCE: Final = 800


def race_frame(circuit: Circuit, race: Race) -> RaceFrame:
    eye = road_height(circuit, race.distance) + EYE_HEIGHT
    horizon = HORIZON + round(eye * FOCAL_LENGTH / SKYLINE_DISTANCE)
    boxes = [
        Box(0, 0, CANVAS_WIDTH, horizon, Colour.SKY),
        Box(0, horizon - PALE_BAND, CANVAS_WIDTH, PALE_BAND, Colour.PALE_SKY),
        *_skyline(circuit, race, horizon - PALE_BAND),
        Box(0, horizon, CANVAS_WIDTH, CANVAS_HEIGHT - horizon, Colour.DARK_GREEN),
    ]
    polygons = road_polygons(circuit, race.distance, race.lateral)
    return RaceFrame(boxes=tuple(boxes), polygons=tuple(polygons))


def _skyline(circuit: Circuit, race: Race, base: int) -> list[Box]:
    strip = SKYLINES[circuit.skyline]
    slide = round(race.heading * FOCAL_LENGTH)
    heights = [strip[(x + slide) % len(strip)] for x in range(CANVAS_WIDTH)]
    boxes: list[Box] = []
    for height, run in groupby(enumerate(heights), key=itemgetter(1)):
        columns = [x for x, _ in run]
        if height:
            boxes.append(
                Box(columns[0], base - height, len(columns), height, Colour.NAVY)
            )
    return boxes
