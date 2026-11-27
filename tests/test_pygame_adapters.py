import pygame

from hotlapper.adapters.circuit_loader import load_circuits
from hotlapper.adapters.pygame_display import PygameDisplay
from hotlapper.adapters.pygame_keyboard import PygameKeyboard
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.menus import (
    TitleItem,
    car_select_frame,
    circuit_select_frame,
    title_frame,
)
from hotlapper.domain.race import start_race
from hotlapper.domain.race_view import race_frame


def test_the_display_opens_draws_the_menus_and_closes() -> None:
    with PygameDisplay() as display:
        display.present(title_frame(TitleItem.START, None))
        display.toggle_fullscreen()
        display.present(circuit_select_frame(load_circuits(), 0, laps=3))
        display.toggle_fullscreen()
        display.present(car_select_frame(0))
        [circuit, *_] = load_circuits()
        display.present(race_frame(circuit, start_race(circuit)))
        assert pygame.display.get_init()

    assert not pygame.display.get_init()


def test_the_keyboard_turns_pygame_events_into_controls() -> None:
    with PygameDisplay():
        keyboard = PygameKeyboard()
        for key in [
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_RIGHT,
            pygame.K_RETURN,
            pygame.K_ESCAPE,
            pygame.K_F11,
            pygame.K_z,
        ]:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        assert keyboard.poll() == Controls(
            commands=(
                Command.UP,
                Command.DOWN,
                Command.LEFT,
                Command.RIGHT,
                Command.CONFIRM,
                Command.BACK,
                Command.FULLSCREEN,
                Command.QUIT,
            )
        )
        assert keyboard.poll() == Controls()
