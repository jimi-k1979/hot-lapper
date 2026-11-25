from hotlapper.adapters.clock import PerfCounterClock
from hotlapper.adapters.pygame_display import PygameDisplay
from hotlapper.adapters.pygame_keyboard import PygameKeyboard
from hotlapper.application.loop import Game


def main() -> None:
    with PygameDisplay() as display:
        Game(PerfCounterClock(), PygameKeyboard(), display).run()


if __name__ == "__main__":
    main()
