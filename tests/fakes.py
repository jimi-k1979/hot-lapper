from collections import deque

from hotlapper.application.ports import Seconds
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import Frame


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
