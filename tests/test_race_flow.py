import pytest

from hotlapper.application.screens import Racing
from hotlapper.domain.circuit import GRID_BOX_LENGTH, OUTER_LIMIT
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import RaceFrame
from hotlapper.domain.race import Race
from tests.fakes import Player, make_circuit

ENTER = Command.CONFIRM
CIRCUIT = make_circuit("Test Park", 1000)
ONE_SECOND = 60


@pytest.fixture
def player() -> Player:
    player = Player([CIRCUIT])
    player.press(ENTER, ENTER, ENTER, ENTER)
    return player


def race(player: Player) -> Race:
    screen = player.game.screen
    assert isinstance(screen, Racing)
    return screen.race


def race_view(player: Player) -> RaceFrame:
    frame = player.frame
    assert isinstance(frame, RaceFrame)
    return frame


def test_confirming_a_car_starts_the_race_on_pole_position(player: Player) -> None:
    pole = CIRCUIT.grid[0]

    assert pole.at - GRID_BOX_LENGTH < race(player).distance < pole.at
    assert race(player).lateral == pole.across
    assert race(player).speed == 0
    race_view(player)


def test_holding_accelerate_gathers_speed(player: Player) -> None:
    player.hold(Controls(accelerate=True))
    player.wait(ONE_SECOND)

    assert race(player).speed > 0


def test_braking_stops_the_car_without_reversing(player: Player) -> None:
    player.hold(Controls(accelerate=True))
    player.wait(ONE_SECOND)
    player.hold(Controls(brake=True))
    player.wait(ONE_SECOND)

    assert race(player).speed == 0


def test_the_brake_wins_over_the_accelerator(player: Player) -> None:
    player.hold(Controls(accelerate=True))
    player.wait(ONE_SECOND)
    speed = race(player).speed
    player.hold(Controls(accelerate=True, brake=True))
    player.wait(ONE_SECOND)

    assert race(player).speed < speed


@pytest.mark.parametrize(
    ("slow", "fast", "direction"),
    [
        pytest.param(
            Controls(steer_left_slow=True),
            Controls(steer_left_fast=True),
            -1,
            id="left",
        ),
        pytest.param(
            Controls(steer_right_slow=True),
            Controls(steer_right_fast=True),
            1,
            id="right",
        ),
    ],
)
def test_steering_moves_the_car_across_the_road_faster_with_the_fast_key(
    player: Player, slow: Controls, fast: Controls, direction: int
) -> None:
    start = race(player).lateral
    player.hold(slow)
    player.wait(10)
    slow_move = (race(player).lateral - start) * direction
    player.hold(fast)
    player.wait(10)
    fast_move = (race(player).lateral - start) * direction - slow_move

    assert 0 < slow_move < fast_move


def test_steering_stops_at_the_outer_limit(player: Player) -> None:
    player.hold(Controls(steer_right_fast=True))
    player.wait(4 * ONE_SECOND)

    assert race(player).lateral == CIRCUIT.width / 2 + OUTER_LIMIT


def test_the_road_moves_towards_the_car_as_it_drives(player: Player) -> None:
    standing = race_view(player).polygons
    player.wait(ONE_SECOND)
    assert race_view(player).polygons == standing

    player.hold(Controls(accelerate=True))
    player.wait(ONE_SECOND)
    assert race_view(player).polygons != standing


def test_closing_the_window_quits_from_a_race(player: Player) -> None:
    player.press(Command.QUIT)

    assert not player.game.running
