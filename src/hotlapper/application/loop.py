from collections.abc import Sequence
from dataclasses import replace
from typing import Final

from hotlapper.application.ports import Clock, Keyboard, Renderer, Seconds
from hotlapper.application.screens import Screen, Title, frame_for, transition
from hotlapper.domain.circuit import Circuit
from hotlapper.domain.controls import Command

STEP: Final[Seconds] = 1 / 60
MAX_STEPS_PER_TICK: Final = 5


class Game:
    def __init__(
        self,
        clock: Clock,
        keyboard: Keyboard,
        renderer: Renderer,
        circuits: Sequence[Circuit],
    ) -> None:
        self._clock = clock
        self._keyboard = keyboard
        self._renderer = renderer
        self._circuits = circuits
        self._screen: Screen | None = Title()
        self._previous = clock.now()
        self._accumulator: Seconds = 0.0
        self._pending: tuple[Command, ...] = ()
        self.steps = 0

    @property
    def screen(self) -> Screen | None:
        return self._screen

    @property
    def running(self) -> bool:
        return self._screen is not None

    def run(self) -> None:
        while self.running:
            self.tick()

    def tick(self) -> None:
        now = self._clock.now()
        self._accumulator += now - self._previous
        self._previous = now

        controls = self._keyboard.poll()
        if Command.FULLSCREEN in controls.commands:
            self._renderer.toggle_fullscreen()
        controls = replace(controls, commands=self._pending + controls.commands)

        steps_this_tick = 0
        while (
            self._screen is not None
            and self._accumulator >= STEP
            and steps_this_tick < MAX_STEPS_PER_TICK
        ):
            self._screen = transition(self._screen, controls, self._circuits)
            controls = replace(controls, commands=())
            self._accumulator -= STEP
            steps_this_tick += 1
            self.steps += 1
        if steps_this_tick == MAX_STEPS_PER_TICK:
            self._accumulator %= STEP
        self._pending = controls.commands

        if self._screen is not None:
            self._renderer.present(frame_for(self._screen, self._circuits))
