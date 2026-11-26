import tomllib
from collections.abc import Mapping
from enum import StrEnum, auto
from importlib.resources import files
from importlib.resources.abc import Traversable
from operator import attrgetter
from typing import Final

from hotlapper.domain.circuit import (
    SEGMENT_LENGTH,
    Circuit,
    CircuitDataError,
    Corner,
    Hazard,
    HazardKind,
    PitArea,
    Point,
    Scenery,
    SceneryKind,
    Section,
    Side,
    Straight,
    build_circuit,
)

PACKAGED: Final = files("hotlapper.adapters.circuits")


class _SectionKind(StrEnum):
    STRAIGHT = auto()
    CORNER = auto()


class _Table:
    def __init__(self, data: Mapping[str, object], path: str = "") -> None:
        self._data = data
        self._path = path

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def only(self, *keys: str) -> None:
        for key in self._data:
            if key not in keys:
                raise CircuitDataError(self._field(key), "is not a known key")

    def string(self, key: str) -> str:
        value = self._get(key)
        if not isinstance(value, str):
            raise CircuitDataError(self._field(key), "should be a string")
        return value

    def integer(self, key: str) -> int:
        value = self._get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise CircuitDataError(self._field(key), "should be a whole number")
        return value

    def number(self, key: str) -> float:
        return _number(self._get(key), self._field(key))

    def segments(self, key: str) -> float:
        value = self.number(key)
        if value < 0 or value % SEGMENT_LENGTH:
            raise CircuitDataError(
                self._field(key), f"should be a whole number of {SEGMENT_LENGTH} m"
            )
        return value

    def choice[E: StrEnum](self, key: str, kind: type[E]) -> E:
        value = self.string(key)
        if value not in kind:
            options = ", ".join(kind)
            raise CircuitDataError(self._field(key), f"should be one of {options}")
        return kind(value)

    def table(self, key: str) -> "_Table":
        value = self._get(key)
        if not isinstance(value, dict):
            raise CircuitDataError(self._field(key), "should be a table")
        return _Table(value, self._field(key))

    def tables(self, key: str) -> list["_Table"]:
        items = self._list(key) if key in self._data else []
        tables: list[_Table] = []
        for index, item in enumerate(items):
            field = f"{self._field(key)}[{index}]"
            if not isinstance(item, dict):
                raise CircuitDataError(field, "should be a table")
            tables.append(_Table(item, field))
        return tables

    def points(self, key: str) -> list[Point]:
        points: list[Point] = []
        for index, item in enumerate(self._list(key)):
            field = f"{self._field(key)}[{index}]"
            if not isinstance(item, list) or len(item) != 2:
                raise CircuitDataError(field, "should be an [x, y] pair")
            x, y = item
            points.append((_number(x, field), _number(y, field)))
        return points

    def _get(self, key: str) -> object:
        if key not in self._data:
            raise CircuitDataError(self._field(key), "is missing")
        return self._data[key]

    def _list(self, key: str) -> list[object]:
        value = self._get(key)
        if not isinstance(value, list):
            raise CircuitDataError(self._field(key), "should be an array")
        return value

    def _field(self, key: str) -> str:
        return f"{self._path}.{key}" if self._path else key


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CircuitDataError(field, "should be a number")
    return float(value)


def load_circuits(directory: Traversable = PACKAGED) -> list[Circuit]:
    circuits = [
        load_circuit(path)
        for path in directory.iterdir()
        if path.name.endswith(".toml")
    ]
    return sorted(circuits, key=attrgetter("order"))


def load_circuit(path: Traversable) -> Circuit:
    try:
        return _circuit(path.name.removesuffix(".toml"), _read(path))
    except CircuitDataError as error:
        error.add_note(f"in circuit file {path.name}")
        raise


def _read(path: Traversable) -> "_Table":
    with path.open("rb") as file:
        try:
            return _Table(tomllib.load(file))
        except tomllib.TOMLDecodeError as error:
            raise CircuitDataError("syntax", str(error)) from error


def _circuit(circuit_id: str, root: _Table) -> Circuit:
    root.only(
        "name",
        "order",
        "width",
        "skyline",
        "outline",
        "pit_area",
        "sections",
        "hazards",
        "scenery",
    )
    return build_circuit(
        circuit_id=circuit_id,
        name=root.string("name"),
        order=root.integer("order"),
        width=root.number("width"),
        skyline=root.string("skyline"),
        sections=[_section(table) for table in root.tables("sections")],
        hazards=[_hazard(table) for table in root.tables("hazards")],
        scenery=[_scenery(table) for table in root.tables("scenery")],
        pit_area=_pit_area(root.table("pit_area")),
        outline=root.points("outline"),
    )


def _section(table: _Table) -> Section:
    climb = table.number("climb") if "climb" in table else 0
    match table.choice("kind", _SectionKind):
        case _SectionKind.STRAIGHT:
            table.only("kind", "length", "climb")
            return Straight(length=table.segments("length"), climb=climb)
        case _SectionKind.CORNER:
            table.only("kind", "turn", "radius", "enter", "hold", "leave", "climb")
            return Corner(
                turn=table.choice("turn", Side),
                radius=table.number("radius"),
                enter=table.segments("enter"),
                hold=table.segments("hold"),
                leave=table.segments("leave"),
                climb=climb,
            )


def _hazard(table: _Table) -> Hazard:
    table.only("kind", "at", "across", "length", "width")
    return Hazard(
        kind=table.choice("kind", HazardKind),
        at=table.number("at"),
        across=table.number("across"),
        length=table.number("length"),
        width=table.number("width"),
    )


def _scenery(table: _Table) -> Scenery:
    table.only("kind", "at", "across")
    return Scenery(
        kind=table.choice("kind", SceneryKind),
        at=table.number("at"),
        across=table.number("across"),
    )


def _pit_area(table: _Table) -> PitArea:
    table.only("side", "at", "length")
    return PitArea(
        side=table.choice("side", Side),
        at=table.number("at"),
        length=table.number("length"),
    )
