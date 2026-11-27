from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Final

from hotlapper.domain.car import CAR_ROSTER
from hotlapper.domain.circuit import Circuit
from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import Frame
from hotlapper.domain.menus import (
    Answer,
    TitleItem,
    car_select_frame,
    circuit_select_frame,
    title_frame,
)
from hotlapper.domain.race import Race, drive, start_race
from hotlapper.domain.race_view import race_frame

FIRST_LAP_COUNT: Final = 3
MIN_LAPS: Final = 1
MAX_LAPS: Final = 15


@dataclass(frozen=True, slots=True)
class Choices:
    circuit: int = 0
    laps: int = FIRST_LAP_COUNT
    car: int = 0


@dataclass(frozen=True, slots=True)
class Title:
    choices: Choices = Choices()
    item: TitleItem = TitleItem.START
    reset: Answer | None = None


@dataclass(frozen=True, slots=True)
class CircuitSelect:
    choices: Choices


@dataclass(frozen=True, slots=True)
class LapCount:
    choices: Choices
    laps: int


@dataclass(frozen=True, slots=True)
class CarSelect:
    choices: Choices


@dataclass(frozen=True, slots=True)
class Racing:
    choices: Choices
    race: Race


type Screen = Title | CircuitSelect | LapCount | CarSelect | Racing


def transition(
    screen: Screen, controls: Controls, circuits: Sequence[Circuit], dt: float
) -> Screen | None:
    next_screen: Screen | None = screen
    for command in controls.commands:
        if next_screen is None:
            break
        next_screen = _on(next_screen, command, circuits)
    match next_screen:
        case Racing(choices=choices, race=race):
            circuit = circuits[choices.circuit]
            return Racing(choices, drive(race, controls, circuit, dt))
    return next_screen


def _on(screen: Screen, command: Command, circuits: Sequence[Circuit]) -> Screen | None:
    if command is Command.QUIT:
        return None
    match screen:
        case Title(reset=None):
            return _title(screen, command)
        case Title():
            return _reset_confirmation(screen, command)
        case CircuitSelect():
            return _circuit_select(screen, command, len(circuits))
        case LapCount():
            return _lap_count(screen, command)
        case CarSelect():
            return _car_select(screen, command, circuits)
        case Racing():
            return screen


def _title(title: Title, command: Command) -> Screen | None:
    items = list(TitleItem)
    match command, title.item:
        case ((Command.UP | Command.DOWN), item):
            index = _moved(items.index(item), command, 0, len(items) - 1)
            return replace(title, item=items[index])
        case Command.CONFIRM, TitleItem.START:
            return CircuitSelect(title.choices)
        case Command.CONFIRM, TitleItem.RESET:
            return replace(title, reset=Answer.NO)
        case (Command.CONFIRM, TitleItem.QUIT) | (Command.BACK, _):
            return None
    return title


def _reset_confirmation(title: Title, command: Command) -> Screen:
    match command:
        case Command.LEFT:
            return replace(title, reset=Answer.YES)
        case Command.RIGHT:
            return replace(title, reset=Answer.NO)
        case Command.CONFIRM | Command.BACK:
            return replace(title, reset=None)
    return title


def _circuit_select(
    select: CircuitSelect, command: Command, circuit_count: int
) -> Screen:
    choices = select.choices
    match command:
        case Command.LEFT | Command.RIGHT:
            circuit = _moved(choices.circuit, command, 0, circuit_count - 1)
            return CircuitSelect(replace(choices, circuit=circuit))
        case Command.CONFIRM:
            return LapCount(choices, choices.laps)
        case Command.BACK:
            return Title(choices)
    return select


def _lap_count(prompt: LapCount, command: Command) -> Screen:
    match command:
        case Command.LEFT | Command.RIGHT:
            laps = _moved(prompt.laps, command, MIN_LAPS, MAX_LAPS)
            return replace(prompt, laps=laps)
        case Command.CONFIRM:
            return CarSelect(replace(prompt.choices, laps=prompt.laps))
        case Command.BACK:
            return CircuitSelect(prompt.choices)
    return prompt


def _car_select(
    select: CarSelect, command: Command, circuits: Sequence[Circuit]
) -> Screen:
    choices = select.choices
    match command:
        case Command.UP | Command.DOWN:
            car = _moved(choices.car, command, 0, len(CAR_ROSTER) - 1)
            return CarSelect(replace(choices, car=car))
        case Command.CONFIRM:
            return Racing(choices, start_race(circuits[choices.circuit]))
        case Command.BACK:
            return CircuitSelect(choices)
    return select


def _moved(value: int, command: Command, lowest: int, highest: int) -> int:
    step = -1 if command in (Command.UP, Command.LEFT) else 1
    return max(lowest, min(value + step, highest))


def frame_for(screen: Screen, circuits: Sequence[Circuit]) -> Frame:
    match screen:
        case Title(item=item, reset=reset):
            return title_frame(item, reset)
        case CircuitSelect(choices=choices):
            return circuit_select_frame(circuits, choices.circuit)
        case LapCount(choices=choices, laps=laps):
            return circuit_select_frame(circuits, choices.circuit, laps)
        case CarSelect(choices=choices):
            return car_select_frame(choices.car)
        case Racing(choices=choices, race=race):
            return race_frame(circuits[choices.circuit], race)
