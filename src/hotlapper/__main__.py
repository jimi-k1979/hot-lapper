from hotlapper.adapters.circuit_loader import load_circuits
from hotlapper.adapters.clock import PerfCounterClock
from hotlapper.adapters.pygame_display import PygameDisplay
from hotlapper.adapters.pygame_keyboard import PygameKeyboard
from hotlapper.application.loop import Game


def main() -> None:
    circuits = load_circuits()
    with PygameDisplay() as display:
        Game(PerfCounterClock(), PygameKeyboard(), display, circuits).run()


if __name__ == "__main__":
    main()
