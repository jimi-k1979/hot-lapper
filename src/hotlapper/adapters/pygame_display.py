from collections.abc import Mapping
from types import TracebackType
from typing import Final, Self, assert_never

import pygame

from hotlapper.domain.canvas import CANVAS_HEIGHT, CANVAS_WIDTH
from hotlapper.domain.font import glyph_rects
from hotlapper.domain.frame import Frame, TitleFrame
from hotlapper.domain.palette import Colour

type RGB = tuple[int, int, int]

EARTHY: Final[Mapping[Colour, RGB]] = {
    Colour.BLACK: (20, 18, 28),
    Colour.WHITE: (236, 236, 224),
    Colour.SKY: (110, 170, 226),
    Colour.PALE_SKY: (196, 220, 236),
    Colour.NAVY: (48, 62, 100),
    Colour.LIGHT_GREEN: (100, 168, 64),
    Colour.DARK_GREEN: (70, 132, 48),
    Colour.FOREST: (36, 90, 50),
    Colour.LIGHT_GREY: (170, 170, 176),
    Colour.MID_GREY: (120, 118, 124),
    Colour.DARK_GREY: (98, 96, 104),
    Colour.RED: (206, 48, 40),
    Colour.AMBER: (238, 180, 44),
    Colour.BROWN: (120, 78, 46),
    Colour.TEAL: (40, 160, 150),
    Colour.BLUE: (40, 110, 200),
}

FRAMES_PER_SECOND: Final = 60
WINDOW_MARGIN: Final = 64
BORDER: Final[RGB] = (0, 0, 0)


def whole_scale(width: int, height: int) -> int:
    return max(1, min(width // CANVAS_WIDTH, height // CANVAS_HEIGHT))


class PygameDisplay:
    def __init__(self) -> None:
        self._fullscreen = False
        self._pacer = pygame.time.Clock()
        self._canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT), depth=8)
        self._canvas.set_palette([EARTHY[colour] for colour in Colour])

    def __enter__(self) -> Self:
        pygame.display.init()
        pygame.display.set_caption("Hot Lapper")
        self._window = self._open_window()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pygame.display.quit()

    def toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        self._window = self._open_window()

    def present(self, frame: Frame) -> None:
        match frame:
            case TitleFrame(background=background, texts=texts):
                self._canvas.fill(background)
                for text in texts:
                    for rect in glyph_rects(text.string, text.x, text.y, text.scale):
                        self._canvas.fill(text.colour, rect)
            case _:
                assert_never(frame)
        self._show_canvas()
        self._pacer.tick(FRAMES_PER_SECOND)

    def _open_window(self) -> pygame.Surface:
        if self._fullscreen:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
        scale = whole_scale(
            desktop_width - WINDOW_MARGIN, desktop_height - WINDOW_MARGIN
        )
        return pygame.display.set_mode((CANVAS_WIDTH * scale, CANVAS_HEIGHT * scale))

    def _show_canvas(self) -> None:
        scale = whole_scale(*self._window.get_size())
        scaled = pygame.transform.scale_by(self._canvas, scale)
        self._window.fill(BORDER)
        self._window.blit(
            scaled, scaled.get_rect(center=self._window.get_rect().center)
        )
        pygame.display.flip()
