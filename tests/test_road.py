import pytest
from hypothesis import given
from hypothesis import strategies as st

from hotlapper.domain.canvas import CANVAS_WIDTH
from hotlapper.domain.circuit import SEGMENT_LENGTH, Circuit, Corner, Side, Straight
from hotlapper.domain.road import (
    DRAW_DISTANCE,
    HORIZON,
    Camera,
    project,
    visible_segments,
)
from tests.fakes import make_circuit

ahead = st.floats(0.5, 2000)
metres = st.floats(-50, 50)
cameras = st.builds(Camera, across=metres, height=st.floats(0, 60))


@given(camera=cameras, ahead=ahead, offset=metres)
def test_a_point_at_eye_height_lies_on_the_horizon(
    camera: Camera, ahead: float, offset: float
) -> None:
    section = project(camera, ahead, offset, camera.height)

    assert section.y == HORIZON


@given(camera=cameras, ahead=ahead, offset=metres, drop=st.floats(0.1, 60))
def test_road_below_the_eye_lies_below_the_horizon(
    camera: Camera, ahead: float, offset: float, drop: float
) -> None:
    section = project(camera, ahead, offset, camera.height - drop)

    assert section.y > HORIZON


@given(
    camera=cameras,
    near=ahead,
    further=st.floats(0.1, 1000),
    offset=metres,
    height=st.floats(-60, 60),
)
def test_road_further_ahead_is_nearer_the_horizon_and_narrower(
    camera: Camera, near: float, further: float, offset: float, height: float
) -> None:
    close = project(camera, near, offset, height)
    far = project(camera, near + further, offset, height)

    assert abs(far.y - HORIZON) <= abs(close.y - HORIZON)
    assert far.scale < close.scale


@given(camera=cameras, ahead=ahead)
def test_road_straight_ahead_is_centred(camera: Camera, ahead: float) -> None:
    section = project(camera, ahead, camera.across, 0)

    assert section.centre == CANVAS_WIDTH / 2


@given(camera=cameras, ahead=ahead, side=st.floats(0, 50))
def test_road_either_side_of_the_camera_is_mirrored(
    camera: Camera, ahead: float, side: float
) -> None:
    left = project(camera, ahead, camera.across - side, 0)
    right = project(camera, ahead, camera.across + side, 0)

    assert abs((left.centre + right.centre) / 2 - CANVAS_WIDTH / 2) < 1e-9


@given(camera=cameras, ahead=ahead, across=metres)
def test_a_metre_across_the_road_spans_scale_pixels(
    camera: Camera, ahead: float, across: float
) -> None:
    section = project(camera, ahead, 0, 0)

    assert abs(section.x(across) - section.x(0) - across * section.scale) < 1e-9


def test_the_view_is_ninety_degrees_wide() -> None:
    section = project(Camera(across=0, height=1), 1, 1, 0)

    assert section.centre == pytest.approx(CANVAS_WIDTH)
    assert section.y == pytest.approx(HORIZON + CANVAS_WIDTH / 2)


SHORT = make_circuit("Tiny Oval", 100)
WINDING = make_circuit(
    "Winding Hill",
    sections=[
        Straight(length=300, climb=10),
        Corner(turn=Side.LEFT, radius=150, enter=20, hold=40, leave=20),
        Straight(length=500, climb=-10),
        Corner(turn=Side.RIGHT, radius=80, enter=10, hold=30, leave=10),
    ],
)
circuits = st.sampled_from([SHORT, WINDING])
eighths_of_a_metre = st.integers(-(10**7), 10**7).map(lambda eighths: eighths / 8)


@given(circuit=circuits, distance=eighths_of_a_metre)
def test_the_draw_distance_is_always_visible_even_on_a_short_circuit(
    circuit: Circuit, distance: float
) -> None:
    assert len(list(visible_segments(circuit, distance))) == DRAW_DISTANCE


@given(circuit=circuits, distance=eighths_of_a_metre)
def test_visible_segments_start_under_the_camera(
    circuit: Circuit, distance: float
) -> None:
    first, _ = next(visible_segments(circuit, distance))

    assert -SEGMENT_LENGTH < first <= 0


@given(circuit=circuits, distance=eighths_of_a_metre)
def test_visible_segments_follow_the_road_round_the_loop(
    circuit: Circuit, distance: float
) -> None:
    for ahead, segment in visible_segments(circuit, distance):
        middle = distance + ahead + SEGMENT_LENGTH / 2
        assert segment is circuit.segment_at(middle)
