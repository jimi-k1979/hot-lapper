from collections import deque
from collections.abc import Sequence
from dataclasses import replace

from hotlapper.application.loop import STEP, Game
from hotlapper.application.ports import Seconds
from hotlapper.domain.circuit import (
    Circuit,
    PitArea,
    Point,
    Section,
    Side,
    Straight,
    build_circuit,
)
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import Frame

TRIANGLE: tuple[Point, ...] = ((0.5, 0.0), (1.0, 1.0), (0.0, 1.0))


def make_circuit(
    name: str, length: float = 1000, sections: Sequence[Section] = ()
) -> Circuit:
    return build_circuit(
        circuit_id=name.lower().replace(" ", "-"),
        name=name,
        order=int(length),
        width=10,
        skyline="airfield",
        sections=sections or [Straight(length=length)],
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
        self.held = Controls()

    def press(self, *commands: Command) -> None:
        self._script.append(replace(self.held, commands=commands))

    def poll(self) -> Controls:
        return self._script.popleft() if self._script else self.held


class RecordingRenderer:
    def __init__(self) -> None:
        self.frames: list[Frame] = []
        self.fullscreen_toggles = 0

    def present(self, frame: Frame) -> None:
        self.frames.append(frame)

    def toggle_fullscreen(self) -> None:
        self.fullscreen_toggles += 1


class Player:
    def __init__(self, circuits: Sequence[Circuit]) -> None:
        self._clock = FakeClock()
        self._keyboard = ScriptedKeyboard()
        self._renderer = RecordingRenderer()
        self.game = Game(self._clock, self._keyboard, self._renderer, circuits)

    def press(self, *commands: Command) -> None:
        for command in commands:
            self._keyboard.press(command)
            steps = self.game.steps
            while self.game.steps == steps:
                self._tick()

    def hold(self, controls: Controls) -> None:
        self._keyboard.held = controls

    def wait(self, steps: int) -> None:
        for _ in range(steps):
            self._tick()

    def _tick(self) -> None:
        self._clock.advance(STEP)
        self.game.tick()

    @property
    def frame(self) -> Frame:
        return self._renderer.frames[-1]
