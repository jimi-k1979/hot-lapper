import math
from collections.abc import Sequence
from itertools import pairwise

from hypothesis import given
from hypothesis import strategies as st

from hotlapper.domain.canvas import CANVAS_HEIGHT, CANVAS_WIDTH
from hotlapper.domain.circuit import Circuit, Corner, Side, Straight
from hotlapper.domain.frame import Polygon, RaceFrame
from hotlapper.domain.palette import Colour
from hotlapper.domain.race import Race
from hotlapper.domain.race_view import race_frame
from hotlapper.domain.road import FOCAL_LENGTH, HORIZON
from hotlapper.domain.skyline import SKYLINE_WIDTH, SKYLINES
from tests.fakes import make_circuit

ROAD = {Colour.MID_GREY, Colour.DARK_GREY}

FLAT = make_circuit("Flat Park", 1000)
HILL = make_circuit(
    "Hill Park",
    sections=[
        Straight(length=100),
        Straight(length=200, climb=12),
        Straight(length=200, climb=-12),
        Straight(length=500),
    ],
)
RING = make_circuit(
    "Ring",
    sections=[
        Straight(length=100),
        Corner(turn=Side.RIGHT, radius=100, enter=5, hold=600, leave=5),
        Straight(length=290),
    ],
)


def frame_at(circuit: Circuit, distance: float, **race: float) -> RaceFrame:
    return race_frame(circuit, Race(distance=distance, **race))


def road(frame: RaceFrame) -> list[Polygon]:
    return [polygon for polygon in frame.polygons if polygon.colour in ROAD]


def top(polygon: Polygon) -> int:
    return min(y for _, y in polygon.points)


def bottom(polygon: Polygon) -> int:
    return max(y for _, y in polygon.points)


def xs(polygon: Polygon) -> list[int]:
    return sorted(x for x, _ in polygon.points)


def coloured(frame: RaceFrame, colours: Sequence[Colour]) -> list[Polygon]:
    return [polygon for polygon in frame.polygons if polygon.colour in colours]


@given(
    circuit=st.sampled_from([FLAT, HILL, RING]),
    distance=st.floats(-5000, 5000),
    lateral=st.floats(-10, 10),
)
def test_road_strips_run_near_to_far_each_wholly_above_the_last(
    circuit: Circuit, distance: float, lateral: float
) -> None:
    strips = road(frame_at(circuit, distance, lateral=lateral))

    for near, far in pairwise(strips):
        assert bottom(far) <= top(near)


@given(distance=st.floats(-5000, 5000), lateral=st.floats(-10, 10))
def test_the_road_reaches_the_bottom_of_the_canvas(
    distance: float, lateral: float
) -> None:
    strips = road(frame_at(FLAT, distance, lateral=lateral))

    assert bottom(strips[0]) >= CANVAS_HEIGHT


def test_a_straight_flat_road_runs_to_the_horizon_centred_on_the_car() -> None:
    strips = road(frame_at(FLAT, 500))

    assert len(strips) > 100
    assert top(strips[-1]) == HORIZON
    for strip in strips:
        left, *_, right = xs(strip)
        assert left + right in (CANVAS_WIDTH - 1, CANVAS_WIDTH, CANVAS_WIDTH + 1)


def test_moving_across_the_road_shifts_it_the_other_way() -> None:
    centred = road(frame_at(FLAT, 500))[5]
    moved_right = road(frame_at(FLAT, 500, lateral=2))[5]

    assert xs(moved_right)[0] < xs(centred)[0]


def test_a_crest_hides_the_road_beyond_it() -> None:
    climbing = road(frame_at(HILL, 120))
    level = road(frame_at(FLAT, 120))

    assert len(climbing) < len(level)


def test_a_right_hand_corner_bends_the_road_right() -> None:
    strips = road(frame_at(RING, 50))

    assert xs(strips[-1])[0] > CANVAS_WIDTH


def test_the_road_does_not_jump_as_the_car_crosses_a_segment_boundary() -> None:
    before = road(frame_at(RING, 400 - 0.01))
    after = road(frame_at(RING, 400 + 0.01))

    for old, new in zip(before[1:30], after[1:30], strict=True):
        for (old_x, old_y), (new_x, new_y) in zip(old.points, new.points, strict=True):
            assert abs(old_x - new_x) <= 1
            assert abs(old_y - new_y) <= 1


def test_grass_kerbs_and_road_change_shade_every_three_segments() -> None:
    frame = frame_at(FLAT, 495.5)
    shades = [
        [polygon.colour for polygon in coloured(frame, colours)][:7]
        for colours in [
            (Colour.LIGHT_GREEN, Colour.DARK_GREEN),
            (Colour.RED, Colour.WHITE),
            (Colour.MID_GREY, Colour.DARK_GREY),
        ]
    ]

    assert shades == [
        [Colour.DARK_GREEN] * 3 + [Colour.LIGHT_GREEN] * 3 + [Colour.DARK_GREEN],
        [Colour.WHITE] * 3 + [Colour.RED] * 3 + [Colour.WHITE],
        [Colour.DARK_GREY] * 3 + [Colour.MID_GREY] * 3 + [Colour.DARK_GREY],
    ]


def test_the_start_finish_line_is_two_rows_of_eight_chequers() -> None:
    chequers = coloured(frame_at(FLAT, 990), [Colour.BLACK, Colour.WHITE])

    blacks = [polygon for polygon in chequers if polygon.colour is Colour.BLACK]
    rows = {bottom(polygon) for polygon in blacks}
    assert len(blacks) == 8
    assert len(rows) == 2


def test_the_grid_is_drawn_in_white_on_both_sides_of_the_road() -> None:
    lines = coloured(frame_at(FLAT, 900), [Colour.WHITE])
    middle = CANVAS_WIDTH / 2

    assert any(max(xs(line)) < middle for line in lines)
    assert any(min(xs(line)) > middle for line in lines)


def test_the_pit_area_is_an_amber_dashed_line_down_the_middle() -> None:
    dashes = coloured(frame_at(FLAT, 0.5), [Colour.AMBER])

    assert len(dashes) >= 5
    for dash in dashes:
        assert min(xs(dash)) <= CANVAS_WIDTH / 2 + 1
        assert max(xs(dash)) >= CANVAS_WIDTH / 2 - 1


def sky(frame: RaceFrame, colour: Colour) -> list[tuple[int, int, int, int]]:
    return [
        (box.x, box.y, box.width, box.height)
        for box in frame.boxes
        if box.colour is colour
    ]


def silhouette(frame: RaceFrame) -> list[int | None]:
    tops: list[int | None] = [None] * CANVAS_WIDTH
    for x, y, width, _ in sky(frame, Colour.NAVY):
        tops[x : x + width] = [y] * width
    return tops


def test_a_pale_band_sits_above_the_horizon_with_the_skyline_on_top() -> None:
    frame = frame_at(FLAT, 500)
    [(_, band_top, _, band_height)] = sky(frame, Colour.PALE_SKY)

    assert band_top + band_height == HORIZON
    assert all(y + height == band_top for _, y, _, height in sky(frame, Colour.NAVY))
    assert any(top is not None for top in silhouette(frame))


def test_the_skyline_slides_as_the_heading_turns() -> None:
    shift = 64
    straight_on = silhouette(frame_at(FLAT, 500))
    turned_right = silhouette(frame_at(FLAT, 500, heading=shift / FOCAL_LENGTH))

    assert turned_right[: CANVAS_WIDTH - shift] == straight_on[shift:]
    assert turned_right != straight_on


def test_the_skyline_drops_as_the_car_climbs() -> None:
    [(_, at_start, _, _)] = sky(frame_at(HILL, 50), Colour.PALE_SKY)
    [(_, on_the_crest, _, _)] = sky(frame_at(HILL, 300), Colour.PALE_SKY)

    assert on_the_crest > at_start


def test_every_skyline_wraps_round_once_per_full_turn() -> None:
    for strip in SKYLINES.values():
        assert len(strip) == SKYLINE_WIDTH == round(math.tau * FOCAL_LENGTH)
