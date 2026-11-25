from typing import Protocol

from hotlapper.domain.controls import Controls
from hotlapper.domain.frame import Frame

type Seconds = float


class Clock(Protocol):
    def now(self) -> Seconds: ...


class Keyboard(Protocol):
    def poll(self) -> Controls: ...


class Renderer(Protocol):
    def present(self, frame: Frame) -> None: ...

    def toggle_fullscreen(self) -> None: ...
