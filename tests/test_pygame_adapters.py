import pygame

from hotlapper.adapters.pygame_display import PygameDisplay
from hotlapper.adapters.pygame_keyboard import PygameKeyboard
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import title_frame


def test_the_display_opens_draws_the_title_and_closes() -> None:
    with PygameDisplay() as display:
        display.present(title_frame())
        display.toggle_fullscreen()
        display.present(title_frame())
        display.toggle_fullscreen()
        assert pygame.display.get_init()

    assert not pygame.display.get_init()


def test_the_keyboard_turns_pygame_events_into_controls() -> None:
    with PygameDisplay():
        keyboard = PygameKeyboard()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        assert keyboard.poll() == Controls(
            commands=(Command.BACK, Command.FULLSCREEN, Command.QUIT)
        )
        assert keyboard.poll() == Controls()
