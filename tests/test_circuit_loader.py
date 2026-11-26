from pathlib import Path

import pytest

from hotlapper.adapters.circuit_loader import (
    PACKAGED_CIRCUITS,
    load_circuit,
    load_circuits,
)
from hotlapper.domain.circuit import (
    CircuitDataError,
    Hazard,
    HazardKind,
    PitArea,
    Scenery,
    SceneryKind,
    Side,
)

VALID = """
name = "Test Park"
order = 2
width = 10
skyline = "hills"
outline = [[0.5, 0.0], [1.0, 1.0], [0.0, 1.0]]

[pit_area]
side = "left"
at = 10
length = 50

[[sections]]
kind = "straight"
length = 500
climb = 4

[[sections]]
kind = "corner"
turn = "right"
radius = 120.5
enter = 20
hold = 40
leave = 20
climb = -4

[[sections]]
kind = "straight"
length = 420

[[hazards]]
kind = "glass"
at = 300
across = -2
length = 5
width = 1.5

[[scenery]]
kind = "barn"
at = 120
across = 25
"""


def write(tmp_path: Path, text: str, stem: str = "test-park") -> Path:
    path = tmp_path / f"{stem}.toml"
    path.write_text(text)
    return path


def test_a_circuit_file_loads_into_a_circuit_named_by_its_stem(tmp_path: Path) -> None:
    circuit = load_circuit(write(tmp_path, VALID))

    assert circuit.circuit_id == "test-park"
    assert circuit.name == "Test Park"
    assert circuit.order == 2
    assert circuit.width == 10
    assert circuit.skyline == "hills"
    assert circuit.length == 1000
    assert circuit.segment_at(520).curve > 0
    assert circuit.segment_at(495).end_height == pytest.approx(4)
    assert circuit.pit_area == PitArea(Side.LEFT, at=10, length=50)
    assert circuit.hazards == (Hazard(HazardKind.GLASS, 300, -2, 5, 1.5),)
    assert circuit.scenery == (Scenery(SceneryKind.BARN, 120, 25),)
    assert circuit.outline == ((0.5, 0.0), (1.0, 1.0), (0.0, 1.0))


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        pytest.param('skyline = "hills"', "", "skyline", id="missing key"),
        pytest.param("radius = 120.5", "", "sections[1].radius", id="missing in table"),
        pytest.param("width = 10", 'width = "wide"', "width", id="string for number"),
        pytest.param("width = 10", "width = true", "width", id="boolean for number"),
        pytest.param("order = 2", "order = 2.5", "order", id="float for integer"),
        pytest.param('name = "Test Park"', "name = 7", "name", id="number for string"),
        pytest.param("[pit_area]", "[pit_area.x]", "pit_area.x", id="nested key"),
        pytest.param("outline = [", "outline = 3 #", "outline", id="not an array"),
        pytest.param(
            'kind = "straight"', 'kind = "hairpin"', "sections[0].kind", id="section"
        ),
        pytest.param('"glass"', '"sand"', "hazards[0].kind", id="hazard kind"),
        pytest.param('"barn"', '"castle"', "scenery[0].kind", id="scenery kind"),
        pytest.param('"right"', '"up"', "sections[1].turn", id="turn"),
        pytest.param("length = 500", "length = 502", "sections[0].length", id="part"),
        pytest.param("enter = 20", "enter = 22.5", "sections[1].enter", id="ramp"),
        pytest.param("[1.0, 1.0]", "[1.0]", "outline[1]", id="point"),
        pytest.param("climb = 4", "clim = 4", "sections[0].clim", id="unknown key"),
        pytest.param('name = "Test Park"', "name = ", "syntax", id="bad toml"),
    ],
)
def test_badly_shaped_files_are_rejected_naming_the_file_and_field(
    tmp_path: Path, old: str, new: str, field: str
) -> None:
    path = write(tmp_path, VALID.replace(old, new, 1))

    with pytest.raises(CircuitDataError) as caught:
        load_circuit(path)

    assert caught.value.field == field
    assert caught.value.file == "test-park.toml"
    assert str(caught.value).startswith(f"test-park.toml: {field}: ")


def test_rule_failures_also_name_the_file(tmp_path: Path) -> None:
    path = write(tmp_path, VALID.replace("across = -2", "across = -9"))

    with pytest.raises(CircuitDataError) as caught:
        load_circuit(path)

    assert caught.value.field == "hazards[0].across"
    assert str(caught.value) == (
        "test-park.toml: hazards[0].across: is not wholly on the road"
    )


def test_a_directory_of_circuits_loads_in_order(tmp_path: Path) -> None:
    write(tmp_path, VALID.replace("order = 2", "order = 9"), stem="later")
    write(tmp_path, VALID.replace("order = 2", "order = 1"), stem="sooner")
    (tmp_path / "notes.txt").write_text("not a circuit")

    circuits = load_circuits(tmp_path)

    assert [circuit.circuit_id for circuit in circuits] == ["sooner", "later"]


def test_every_packaged_circuit_loads() -> None:
    circuits = load_circuits()

    assert len({circuit.circuit_id for circuit in circuits}) == len(circuits)


def test_westwood_aerodrome_is_a_flat_4780_m_circuit() -> None:
    westwood = load_circuit(PACKAGED_CIRCUITS / "westwood-aerodrome.toml")

    assert westwood.name == "Westwood Aerodrome"
    assert westwood.length == 4780
    assert all(segment.height == 0 for segment in westwood.segments)
    assert 5 <= len(westwood.hazards) <= 8
    assert 12 <= len(westwood.outline) <= 30
