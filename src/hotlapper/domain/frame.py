from dataclasses import dataclass

from hotlapper.domain.canvas import CANVAS_WIDTH
from hotlapper.domain.font import text_width
from hotlapper.domain.palette import Colour


@dataclass(frozen=True, slots=True)
class Text:
    x: int
    y: int
    string: str
    colour: Colour
    scale: int = 1


@dataclass(frozen=True, slots=True)
class TitleFrame:
    background: Colour
    texts: tuple[Text, ...]


type Frame = TitleFrame

_TITLE = "HOT LAPPER"
_TITLE_SCALE = 3


def title_frame() -> TitleFrame:
    x = (CANVAS_WIDTH - text_width(_TITLE, _TITLE_SCALE)) // 2
    title = Text(x=x, y=60, string=_TITLE, colour=Colour.AMBER, scale=_TITLE_SCALE)
    return TitleFrame(background=Colour.BLACK, texts=(title,))
