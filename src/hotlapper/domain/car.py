from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Final

from hotlapper.domain.palette import Colour


class Transmission(StrEnum):
    AUTOMATIC = auto()
    MANUAL = auto()


@dataclass(frozen=True, slots=True)
class Car:
    name: str
    transmission: Transmission
    colour: Colour
    description: str
    target_lap_seconds: float
    target_tyre_life_km: float


CAR_ROSTER: Final = (
    Car(
        name="STALWART",
        transmission=Transmission.AUTOMATIC,
        colour=Colour.TEAL,
        description="TOUGH AND SIMPLE: IT CHANGES GEAR ITSELF",
        target_lap_seconds=95,
        target_tyre_life_km=120,
    ),
    Car(
        name="MERIDIAN",
        transmission=Transmission.MANUAL,
        colour=Colour.RED,
        description="QUICK AND FORGIVING IN EQUAL MEASURE",
        target_lap_seconds=77,
        target_tyre_life_km=80,
    ),
    Car(
        name="KESTREL",
        transmission=Transmission.MANUAL,
        colour=Colour.BLUE,
        description="BLISTERING PACE FOR A PERFECT DRIVER",
        target_lap_seconds=70,
        target_tyre_life_km=50,
    ),
)


def pace(car: Car) -> float:
    fastest = min(other.target_lap_seconds for other in CAR_ROSTER)
    return fastest / car.target_lap_seconds


def durability(car: Car) -> float:
    longest = max(other.target_tyre_life_km for other in CAR_ROSTER)
    return car.target_tyre_life_km / longest
