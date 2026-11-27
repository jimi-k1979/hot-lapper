import pytest

from hotlapper.application.screens import (
    CarSelect,
    Choices,
    CircuitSelect,
    LapCount,
    Title,
)
from hotlapper.domain.controls import Command
from hotlapper.domain.font import GLYPHS
from hotlapper.domain.frame import Box, MenuFrame
from hotlapper.domain.menus import BAR_HEIGHT, Answer, TitleItem
from hotlapper.domain.palette import Colour
from tests.fakes import Player, make_circuit

UP, DOWN, LEFT, RIGHT = Command.UP, Command.DOWN, Command.LEFT, Command.RIGHT
ENTER, ESC = Command.CONFIRM, Command.BACK

CIRCUITS = (
    make_circuit("Short Park", 1000),
    make_circuit("Middle Ring", 2000),
    make_circuit("Long Way Round", 3000),
)


@pytest.fixture
def player() -> Player:
    return Player(CIRCUITS)


def test_enter_on_start_opens_circuit_select(player: Player) -> None:
    player.press(ENTER)

    assert player.game.screen == CircuitSelect(Choices())


def test_quit_on_the_title_menu_quits(player: Player) -> None:
    player.press(DOWN, DOWN, ENTER)

    assert not player.game.running


def test_the_title_menu_stops_at_its_ends(player: Player) -> None:
    player.press(UP)
    assert player.game.screen == Title(item=TitleItem.START)

    player.press(DOWN, DOWN, DOWN)
    assert player.game.screen == Title(item=TitleItem.QUIT)


def test_reset_lap_records_asks_for_confirmation_defaulting_to_no(
    player: Player,
) -> None:
    player.press(DOWN, ENTER)

    assert player.game.screen == Title(item=TitleItem.RESET, reset=Answer.NO)


def test_the_reset_confirmation_moves_between_yes_and_no(player: Player) -> None:
    player.press(DOWN, ENTER, LEFT)
    assert player.game.screen == Title(item=TitleItem.RESET, reset=Answer.YES)

    player.press(RIGHT)
    assert player.game.screen == Title(item=TitleItem.RESET, reset=Answer.NO)


@pytest.mark.parametrize(
    "answer",
    [pytest.param([LEFT, ENTER], id="yes"), pytest.param([ENTER], id="no")],
)
def test_answering_the_reset_confirmation_returns_to_the_title_menu(
    player: Player, answer: list[Command]
) -> None:
    player.press(DOWN, ENTER, *answer)

    assert player.game.screen == Title(item=TitleItem.RESET)


def test_esc_backs_out_of_the_reset_confirmation_without_quitting(
    player: Player,
) -> None:
    player.press(DOWN, ENTER, ESC)

    assert player.game.screen == Title(item=TitleItem.RESET)


def test_left_and_right_choose_a_circuit_stopping_at_the_ends(player: Player) -> None:
    player.press(ENTER, LEFT)
    assert player.game.screen == CircuitSelect(Choices(circuit=0))

    player.press(RIGHT, RIGHT, RIGHT)
    assert player.game.screen == CircuitSelect(Choices(circuit=2))


def test_esc_on_circuit_select_returns_to_the_title_screen(player: Player) -> None:
    player.press(ENTER, RIGHT, ESC)

    assert player.game.screen == Title(Choices(circuit=1))


def test_enter_on_a_circuit_opens_the_lap_count_prompt_at_three(
    player: Player,
) -> None:
    player.press(ENTER, ENTER)

    assert player.game.screen == LapCount(Choices(), laps=3)


def test_the_lap_count_runs_from_1_to_15_and_stops_at_the_ends(
    player: Player,
) -> None:
    player.press(ENTER, ENTER, *[LEFT] * 3)
    assert player.game.screen == LapCount(Choices(), laps=1)

    player.press(*[RIGHT] * 20)
    assert player.game.screen == LapCount(Choices(), laps=15)


def test_esc_backs_out_of_the_lap_count_prompt_forgetting_the_count(
    player: Player,
) -> None:
    player.press(ENTER, ENTER, RIGHT, ESC)

    assert player.game.screen == CircuitSelect(Choices())


def test_enter_on_the_lap_count_opens_car_select(player: Player) -> None:
    player.press(ENTER, RIGHT, ENTER, RIGHT, ENTER)

    assert player.game.screen == CarSelect(Choices(circuit=1, laps=4))


def test_up_and_down_choose_a_car_stopping_at_the_ends(player: Player) -> None:
    player.press(ENTER, ENTER, ENTER, UP)
    assert player.game.screen == CarSelect(Choices(car=0))

    player.press(DOWN, DOWN, DOWN)
    assert player.game.screen == CarSelect(Choices(car=2))


def test_esc_on_car_select_returns_to_circuit_select(player: Player) -> None:
    player.press(ENTER, ENTER, ENTER, DOWN, ESC)

    assert player.game.screen == CircuitSelect(Choices(car=1))


@pytest.mark.parametrize(
    "route",
    [
        pytest.param([], id="title"),
        pytest.param([DOWN, ENTER], id="reset confirmation"),
        pytest.param([ENTER], id="circuit select"),
        pytest.param([ENTER, ENTER], id="lap count"),
        pytest.param([ENTER, ENTER, ENTER], id="car select"),
    ],
)
def test_closing_the_window_quits_from_every_menu(
    player: Player, route: list[Command]
) -> None:
    player.press(*route, Command.QUIT)

    assert not player.game.running


def test_last_choices_are_remembered_between_visits(player: Player) -> None:
    player.press(ENTER, RIGHT, RIGHT, ENTER, LEFT, ENTER, DOWN, ESC, ESC)
    choices = Choices(circuit=2, laps=2, car=1)

    screens = []
    for _ in range(3):
        player.press(ENTER)
        screens.append(player.game.screen)

    assert screens == [
        CircuitSelect(choices),
        LapCount(choices, laps=2),
        CarSelect(choices),
    ]


def menu(player: Player) -> MenuFrame:
    frame = player.frame
    assert isinstance(frame, MenuFrame)
    assert set("".join(text.string for text in frame.texts)) <= GLYPHS.keys()
    return frame


def strings(frame: MenuFrame) -> list[str]:
    return [text.string for text in frame.texts]


def highlighted(frame: MenuFrame) -> list[str]:
    return [text.string for text in frame.texts if text.colour is Colour.AMBER]


def test_the_title_screen_offers_its_menu_and_lists_the_controls(
    player: Player,
) -> None:
    player.press(DOWN)
    frame = menu(player)

    assert strings(frame)[:4] == ["HOT LAPPER", "START", "RESET LAP RECORDS", "QUIT"]
    assert highlighted(frame)[1:] == ["RESET LAP RECORDS"]
    for keys in ["A S D F", "I K", "J L", "F11", "ESC", "ENTER"]:
        assert any(string.startswith(keys) for string in strings(frame))


def test_the_reset_confirmation_asks_yes_or_no(player: Player) -> None:
    player.press(DOWN, ENTER, LEFT)
    frame = menu(player)

    assert "RESET ALL LAP RECORDS?" in strings(frame)
    assert {"YES", "NO"} <= set(strings(frame))
    assert "YES" in highlighted(frame)
    assert "START" not in strings(frame)


def test_circuit_select_shows_every_circuit_with_an_unset_lap_record(
    player: Player,
) -> None:
    player.press(ENTER, RIGHT)
    frame = menu(player)

    assert strings(frame)[0] == "CHOOSE A CIRCUIT"
    names = ["SHORT PARK", "MIDDLE RING", "LONG WAY", "ROUND"]
    assert [string for string in strings(frame) if string in names] == names
    assert strings(frame).count("--:--.--") == 3
    assert "MIDDLE RING" in highlighted(frame)


def test_each_circuit_map_is_a_thin_white_closed_outline(player: Player) -> None:
    player.press(ENTER)
    frame = menu(player)

    assert len(frame.lines) == 3 * 3
    assert all(line.colour is Colour.WHITE for line in frame.lines)
    first_map = frame.lines[:3]
    assert first_map[-1].end == first_map[0].start


def test_each_circuit_map_has_a_chequered_marker_at_its_start(
    player: Player,
) -> None:
    player.press(ENTER)
    frame = menu(player)

    for line in frame.lines[::3]:
        [marker] = [box for box in frame.boxes if inside(line.start, box)]
        squares = [
            box
            for box in frame.boxes
            if box.colour is Colour.BLACK and inside((box.x, box.y), marker)
        ]
        assert marker.colour is Colour.WHITE
        assert len(squares) == 4


def inside(point: tuple[int, int], box: Box) -> bool:
    x, y = point
    return box.x <= x < box.x + box.width and box.y <= y < box.y + box.height


def test_the_lap_count_prompt_shows_the_count_on_circuit_select(
    player: Player,
) -> None:
    player.press(ENTER, ENTER, RIGHT)
    frame = menu(player)

    assert strings(frame)[0] == "CHOOSE A CIRCUIT"
    assert "LAPS  < 4 >" in highlighted(frame)


def test_car_select_shows_each_car_with_its_bars(player: Player) -> None:
    player.press(ENTER, ENTER, ENTER, DOWN, DOWN)
    frame = menu(player)

    assert strings(frame)[0] == "CHOOSE A CAR"
    for name, transmission in [
        ("STALWART", "AUTOMATIC"),
        ("MERIDIAN", "MANUAL"),
        ("KESTREL", "MANUAL"),
    ]:
        index = strings(frame).index(name)
        assert strings(frame)[index + 1] == transmission
    assert "KESTREL" in highlighted(frame)
    assert bar_fills(frame, Colour.AMBER) == [66, 82, 90]
    assert bar_fills(frame, Colour.LIGHT_GREEN) == [90, 60, 38]


def bar_fills(frame: MenuFrame, colour: Colour) -> list[int]:
    return [
        box.width
        for box in frame.boxes
        if box.colour is colour and box.height == BAR_HEIGHT
    ]


def test_each_car_picture_is_drawn_in_its_colour(player: Player) -> None:
    player.press(ENTER, ENTER, ENTER)
    colours = {box.colour for box in menu(player).boxes}

    assert {Colour.TEAL, Colour.RED, Colour.BLUE} <= colours
