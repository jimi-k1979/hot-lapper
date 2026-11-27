from dataclasses import dataclass
from typing import Final

from hotlapper.domain.circuit import GRID_BOX_LENGTH, OUTER_LIMIT, Circuit, Metres
from hotlapper.domain.controls import Controls

ACCELERATION: Final = 8.0
BRAKING: Final = 20.0
TOP_SPEED: Final = 80.0
SLOW_STEER: Final = 2.0
FAST_STEER: Final = 5.0


@dataclass(frozen=True, slots=True)
class Race:
    distance: Metres
    lateral: Metres = 0
    speed: float = 0
    heading: float = 0


def start_race(circuit: Circuit) -> Race:
    pole = circuit.grid[0]
    return Race(distance=pole.at - GRID_BOX_LENGTH / 2, lateral=pole.across)


def drive(race: Race, controls: Controls, circuit: Circuit, dt: float) -> Race:
    if controls.brake:
        speed = max(0.0, race.speed - BRAKING * dt)
    elif controls.accelerate:
        speed = min(TOP_SPEED, race.speed + ACCELERATION * dt)
    else:
        speed = race.speed
    travelled = speed * dt
    limit = circuit.width / 2 + OUTER_LIMIT
    lateral = race.lateral + _steering(controls) * dt
    return Race(
        distance=(race.distance + travelled) % circuit.length,
        lateral=max(-limit, min(lateral, limit)),
        speed=speed,
        heading=race.heading + circuit.segment_at(race.distance).curve * travelled,
    )


def _steering(controls: Controls) -> float:
    return FAST_STEER * (
        controls.steer_right_fast - controls.steer_left_fast
    ) + SLOW_STEER * (controls.steer_right_slow - controls.steer_left_slow)
