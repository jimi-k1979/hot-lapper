from collections import deque

from hotlapper.application.ports import Seconds
from hotlapper.domain.circuit import (
    Circuit,
    PitArea,
    Point,
    Side,
    Straight,
    build_circuit,
)
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import Frame

TRIANGLE: tuple[Point, ...] = ((0.5, 0.0), (1.0, 1.0), (0.0, 1.0))


def make_circuit(name: str, length: float = 1000) -> Circuit:
    return build_circuit(
        circuit_id=name.lower().replace(" ", "-"),
        name=name,
        order=int(length),
        width=10,
        skyline="hills",
        sections=[Straight(length=length)],
        hazards=[],
        scenery=[],
        pit_area=PitArea(side=Side.RIGHT, at=10, length=50),
        outline=TRIANGLE,
    )


class FakeClock:
    def __init__(self) -> None:
        self._now: Seconds = 0.0

    def now(self) -> Seconds:
        return self._now

    def advance(self, seconds: Seconds) -> None:
        self._now += seconds


class ScriptedKeyboard:
    def __init__(self) -> None:
        self._script: deque[Controls] = deque()

    def press(self, *commands: Command) -> None:
        self._script.append(Controls(commands=commands))

    def poll(self) -> Controls:
        return self._script.popleft() if self._script else Controls()


class RecordingRenderer:
    def __init__(self) -> None:
        self.frames: list[Frame] = []
        self.fullscreen_toggles = 0

    def present(self, frame: Frame) -> None:
        self.frames.append(frame)

    def toggle_fullscreen(self) -> None:
        self.fullscreen_toggles += 1
