from dataclasses import dataclass
from enum import Enum, auto


class Command(Enum):
    BACK = auto()
    FULLSCREEN = auto()
    QUIT = auto()


@dataclass(frozen=True, slots=True)
class Controls:
    steer_left_fast: bool = False
    steer_left_slow: bool = False
    steer_right_slow: bool = False
    steer_right_fast: bool = False
    accelerate: bool = False
    brake: bool = False
    commands: tuple[Command, ...] = ()
