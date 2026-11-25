from dataclasses import dataclass

from hotlapper.domain.controls import Command, Controls
from hotlapper.domain.frame import Frame, title_frame


@dataclass(frozen=True, slots=True)
class Title:
    pass


type Screen = Title


def transition(screen: Screen, controls: Controls) -> Screen | None:
    if Command.QUIT in controls.commands:
        return None
    match screen:
        case Title():
            return None if Command.BACK in controls.commands else screen


def frame_for(screen: Screen) -> Frame:
    match screen:
        case Title():
            return title_frame()
