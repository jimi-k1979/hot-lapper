from collections.abc import Sequence
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hotlapper.domain.circuit import (
    Circuit,
    CircuitDataError,
    Corner,
    CornerArrow,
    GridBox,
    Hazard,
    HazardKind,
    PitArea,
    Point,
    Scenery,
    SceneryKind,
    Section,
    Side,
    Straight,
    build_circuit,
)

SQUARE: tuple[Point, ...] = ((0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
RIGHT_PITS = PitArea(side=Side.RIGHT, at=10, length=50)


def build(
    sections: Sequence[Section] = (Straight(length=1000),),
    *,
    hazards: Sequence[Hazard] = (),
    scenery: Sequence[Scenery] = (),
    pit_area: PitArea = RIGHT_PITS,
    outline: Sequence[Point] = SQUARE,
) -> Circuit:
    return build_circuit(
        circuit_id="test-park",
        name="Test Park",
        order=1,
        width=10,
        skyline="hills",
        sections=sections,
        hazards=hazards,
        scenery=scenery,
        pit_area=pit_area,
        outline=outline,
    )


def test_straights_expand_into_five_metre_segments() -> None:
    circuit = build([Straight(length=600), Straight(length=400)])

    assert circuit.length == 1000
    assert len(circuit.segments) == 200
    assert [segment.start for segment in circuit.segments[:3]] == [0, 5, 10]
    assert all(segment.curve == 0 for segment in circuit.segments)


def test_corner_curvature_ramps_through_enter_and_leave() -> None:
    corner = Corner(turn=Side.RIGHT, radius=100, enter=20, hold=10, leave=20)
    circuit = build([corner, Straight(length=950)])

    curves = [segment.curve for segment in circuit.segments[:11]]

    entering = [0.00125, 0.00375, 0.00625, 0.00875]
    holding = [0.01, 0.01]
    leaving = [0.00875, 0.00625, 0.00375, 0.00125]
    assert curves == pytest.approx([*entering, *holding, *leaving, 0])


def test_left_corners_curve_negatively() -> None:
    corner = Corner(turn=Side.LEFT, radius=50, enter=0, hold=10, leave=0)
    circuit = build([corner, Straight(length=990)])

    assert [segment.curve for segment in circuit.segments[:2]] == [-0.02, -0.02]


def test_climbs_ease_in_and_out_along_an_s_curve() -> None:
    circuit = build(
        [
            Straight(length=100, climb=5),
            Straight(length=100, climb=-5),
            Straight(length=800),
        ]
    )
    segments = circuit.segments

    assert segments[0].height == 0
    assert segments[0].end_height == pytest.approx(0.03625)
    assert segments[10].height == pytest.approx(2.5)
    assert segments[19].end_height == pytest.approx(5)
    assert segments[20].height == pytest.approx(5)
    assert segments[30].height == pytest.approx(2.5)
    assert segments[40].height == pytest.approx(0)


def test_colour_bands_alternate_every_three_segments() -> None:
    circuit = build()

    bands = [segment.light_band for segment in circuit.segments[:9]]

    assert bands == [True] * 3 + [False] * 3 + [True] * 3


WINDING = build(
    [
        Straight(length=300, climb=10),
        Corner(turn=Side.LEFT, radius=150, enter=20, hold=40, leave=20),
        Straight(length=500, climb=-10),
        Corner(turn=Side.RIGHT, radius=80, enter=10, hold=30, leave=10),
    ]
)
eighths_of_a_metre = st.integers(-(10**7), 10**7).map(lambda eighths: eighths / 8)


@given(distance=eighths_of_a_metre, laps=st.integers(-50, 50))
def test_segment_lookup_repeats_every_lap(distance: float, laps: int) -> None:
    later = distance + laps * WINDING.length

    assert WINDING.segment_at(later) == WINDING.segment_at(distance)


@given(distance=eighths_of_a_metre)
def test_segment_lookup_finds_the_segment_under_the_distance(distance: float) -> None:
    segment = WINDING.segment_at(distance)

    assert segment.start <= distance % WINDING.length < segment.start + 5


def test_a_hair_before_the_line_is_the_last_segment() -> None:
    assert WINDING.segment_at(-1e-20) == WINDING.segments[-1]


def test_the_grid_is_five_staggered_rows_behind_the_line() -> None:
    circuit = build(pit_area=PitArea(side=Side.RIGHT, at=10, length=50))

    assert circuit.grid == (
        GridBox(at=995, across=-2.5),
        GridBox(at=987, across=2.5),
        GridBox(at=979, across=-2.5),
        GridBox(at=971, across=2.5),
        GridBox(at=963, across=-2.5),
        GridBox(at=955, across=2.5),
        GridBox(at=947, across=-2.5),
        GridBox(at=939, across=2.5),
        GridBox(at=931, across=-2.5),
        GridBox(at=923, across=2.5),
    )


def test_pole_position_is_on_the_side_away_from_the_pit_area() -> None:
    circuit = build(pit_area=PitArea(side=Side.LEFT, at=10, length=50))

    assert circuit.grid[0] == GridBox(at=995, across=2.5)


def test_sharp_corners_get_arrows_on_the_outside_of_the_approach() -> None:
    corner = Corner(turn=Side.RIGHT, radius=100, enter=20, hold=40, leave=20)
    circuit = build([Straight(length=500), corner, Straight(length=420)])

    assert circuit.corner_arrows == (
        CornerArrow(at=350, across=-13, turn=Side.RIGHT),
        CornerArrow(at=400, across=-13, turn=Side.RIGHT),
        CornerArrow(at=450, across=-13, turn=Side.RIGHT),
    )


def test_gentle_corners_get_no_arrows() -> None:
    corner = Corner(turn=Side.RIGHT, radius=200, enter=20, hold=40, leave=20)
    circuit = build([Straight(length=500), corner, Straight(length=420)])

    assert circuit.corner_arrows == ()


def test_arrows_for_a_corner_just_after_the_line_stand_before_it() -> None:
    corner = Corner(turn=Side.LEFT, radius=50, enter=10, hold=10, leave=10)
    circuit = build([corner, Straight(length=970)])

    assert circuit.corner_arrows == (
        CornerArrow(at=850, across=13, turn=Side.LEFT),
        CornerArrow(at=900, across=13, turn=Side.LEFT),
        CornerArrow(at=950, across=13, turn=Side.LEFT),
    )


def rejected_field(**circuit: Any) -> str:
    with pytest.raises(CircuitDataError) as caught:
        build(**circuit)
    return caught.value.field


def test_gradients_steeper_than_the_cap_are_rejected() -> None:
    steep = [Straight(100, climb=8), Straight(100, climb=-8), Straight(800)]

    assert rejected_field(sections=steep) == "sections[0].climb"


def test_climbs_that_do_not_return_to_the_start_height_are_rejected() -> None:
    uphill = [Straight(500, climb=5), Straight(500)]

    assert rejected_field(sections=uphill) == "sections"


def oil(at: float, across: float = 0, length: float = 10, width: float = 2) -> Hazard:
    return Hazard(HazardKind.OIL, at=at, across=across, length=length, width=width)


@pytest.mark.parametrize(
    ("hazard", "field"),
    [
        pytest.param(oil(300, across=4, width=3), "hazards[0].across", id="right edge"),
        pytest.param(oil(300, across=-4, width=3), "hazards[0].across", id="left edge"),
        pytest.param(oil(-5), "hazards[0].at", id="before the line"),
        pytest.param(oil(995), "hazards[0].at", id="past the end"),
        pytest.param(oil(910), "hazards[0].at", id="on the grid"),
        pytest.param(oil(55), "hazards[0].at", id="in the pit area"),
    ],
)
def test_hazards_off_the_road_or_in_the_way_are_rejected(
    hazard: Hazard, field: str
) -> None:
    assert rejected_field(hazards=[hazard]) == field


def test_hazards_may_touch_the_road_edge_the_pit_area_and_the_grid() -> None:
    hazards = [oil(60, across=3.5, width=3), oil(908, across=-3.5, width=3)]

    assert build(hazards=hazards).hazards == tuple(hazards)


def tree(at: float, across: float) -> Scenery:
    return Scenery(SceneryKind.TREE, at=at, across=across)


@pytest.mark.parametrize(
    ("scenery", "field"),
    [
        pytest.param(tree(300, across=11), "scenery[0].across", id="on the limit"),
        pytest.param(tree(300, across=-8), "scenery[0].across", id="inside it"),
        pytest.param(tree(-1, across=20), "scenery[0].at", id="before the line"),
        pytest.param(tree(1000, across=20), "scenery[0].at", id="past the end"),
    ],
)
def test_scenery_within_the_outer_limit_or_off_the_circuit_is_rejected(
    scenery: Scenery, field: str
) -> None:
    assert rejected_field(scenery=[scenery]) == field


def test_scenery_beyond_the_outer_limit_is_kept() -> None:
    scenery = [tree(0, across=11.5), tree(999, across=-30)]

    assert build(scenery=scenery).scenery == tuple(scenery)


@pytest.mark.parametrize(
    ("pit_area", "field"),
    [
        (PitArea(Side.LEFT, at=-10, length=50), "pit_area.at"),
        (PitArea(Side.LEFT, at=960, length=50), "pit_area.length"),
    ],
)
def test_a_pit_area_outside_the_circuit_is_rejected(
    pit_area: PitArea, field: str
) -> None:
    assert rejected_field(pit_area=pit_area) == field


@pytest.mark.parametrize(
    ("outline", "field"),
    [
        pytest.param([(0.5, 0.0), (1.0, 1.0)], "outline", id="two points"),
        pytest.param([(0.5, 0.0), (1.2, 1.0), (0.0, 1.0)], "outline[1]", id="outside"),
        pytest.param([(0.5, 0.0), (1.0, 1.0), (0.0, -0.1)], "outline[2]", id="below"),
    ],
)
def test_an_outline_that_is_not_a_polygon_in_the_unit_square_is_rejected(
    outline: list[Point], field: str
) -> None:
    assert rejected_field(outline=outline) == field


def test_a_circuit_without_sections_is_rejected() -> None:
    assert rejected_field(sections=[]) == "sections"


def test_corners_without_a_positive_radius_are_rejected() -> None:
    flat = Corner(turn=Side.LEFT, radius=0, enter=10, hold=10, leave=10)

    assert rejected_field(sections=[Straight(970), flat]) == "sections[1].radius"
