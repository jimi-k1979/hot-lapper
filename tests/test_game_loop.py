import pytest

from hotlapper.application.loop import STEP, Game
from hotlapper.domain.controls import Command
from hotlapper.domain.frame import MenuFrame
from tests.fakes import FakeClock, RecordingRenderer, ScriptedKeyboard, make_circuit


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def keyboard() -> ScriptedKeyboard:
    return ScriptedKeyboard()


@pytest.fixture
def renderer() -> RecordingRenderer:
    return RecordingRenderer()


@pytest.fixture
def game(
    clock: FakeClock, keyboard: ScriptedKeyboard, renderer: RecordingRenderer
) -> Game:
    return Game(clock, keyboard, renderer, [make_circuit("Test Park")])


def test_the_game_starts_on_the_title_screen(
    game: Game, clock: FakeClock, renderer: RecordingRenderer
) -> None:
    clock.advance(STEP)
    game.tick()

    [frame] = renderer.frames
    assert isinstance(frame, MenuFrame)
    assert frame.texts[0].string == "HOT LAPPER"


def test_a_tick_runs_one_fixed_step_per_sixtieth_of_a_second(
    game: Game, clock: FakeClock
) -> None:
    clock.advance(3 * STEP)
    game.tick()

    assert game.steps == 3


def test_a_tick_shorter_than_a_step_runs_no_step_but_still_presents(
    game: Game, clock: FakeClock, renderer: RecordingRenderer
) -> None:
    clock.advance(STEP / 2)
    game.tick()

    assert game.steps == 0
    assert len(renderer.frames) == 1


def test_leftover_time_carries_into_the_next_tick(game: Game, clock: FakeClock) -> None:
    clock.advance(STEP * 0.6)
    game.tick()
    clock.advance(STEP * 0.6)
    game.tick()

    assert game.steps == 1


def test_a_long_stall_runs_at_most_five_catch_up_steps(
    game: Game, clock: FakeClock
) -> None:
    clock.advance(1.0)
    game.tick()

    assert game.steps == 5


def test_the_backlog_beyond_the_catch_up_cap_is_dropped(
    game: Game, clock: FakeClock
) -> None:
    clock.advance(1.0)
    game.tick()
    clock.advance(STEP)
    game.tick()

    assert game.steps == 6


def test_esc_on_the_title_screen_quits(
    game: Game, clock: FakeClock, keyboard: ScriptedKeyboard
) -> None:
    keyboard.press(Command.BACK)
    clock.advance(STEP)
    game.tick()

    assert not game.running


def test_closing_the_window_quits(
    game: Game, clock: FakeClock, keyboard: ScriptedKeyboard
) -> None:
    keyboard.press(Command.QUIT)
    clock.advance(STEP)
    game.tick()

    assert not game.running


def test_no_frame_is_presented_once_the_game_has_quit(
    game: Game,
    clock: FakeClock,
    keyboard: ScriptedKeyboard,
    renderer: RecordingRenderer,
) -> None:
    keyboard.press(Command.QUIT)
    clock.advance(STEP)
    game.tick()

    assert renderer.frames == []


def test_run_returns_when_the_game_quits(
    game: Game, clock: FakeClock, keyboard: ScriptedKeyboard
) -> None:
    keyboard.press(Command.QUIT)
    clock.advance(STEP)

    game.run()

    assert game.steps == 1


def test_an_edge_command_waits_for_a_tick_that_runs_a_step(
    game: Game, clock: FakeClock, keyboard: ScriptedKeyboard
) -> None:
    keyboard.press(Command.BACK)
    clock.advance(STEP / 2)
    game.tick()
    assert game.running

    clock.advance(STEP / 2)
    game.tick()
    assert not game.running


def test_f11_toggles_fullscreen_without_leaving_the_title_screen(
    game: Game,
    clock: FakeClock,
    keyboard: ScriptedKeyboard,
    renderer: RecordingRenderer,
) -> None:
    keyboard.press(Command.FULLSCREEN)
    clock.advance(STEP)
    game.tick()

    assert renderer.fullscreen_toggles == 1
    assert game.running
