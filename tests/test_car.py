import pytest

from hotlapper.domain.car import CAR_ROSTER, Transmission, durability, pace
from hotlapper.domain.palette import Colour


def test_the_roster_is_a_teal_automatic_a_red_manual_and_a_blue_manual() -> None:
    assert [(car.transmission, car.colour) for car in CAR_ROSTER] == [
        (Transmission.AUTOMATIC, Colour.TEAL),
        (Transmission.MANUAL, Colour.RED),
        (Transmission.MANUAL, Colour.BLUE),
    ]


def test_pace_is_the_fastest_target_lap_over_each_cars_target_lap() -> None:
    automatic, balanced, fast = CAR_ROSTER

    assert pace(fast) == 1
    assert pace(balanced) == pytest.approx(70 / 77)
    assert pace(automatic) == pytest.approx(70 / 95)


def test_durability_is_each_cars_tyre_life_over_the_longest() -> None:
    automatic, balanced, fast = CAR_ROSTER

    assert durability(automatic) == 1
    assert durability(balanced) == pytest.approx(80 / 120)
    assert durability(fast) == pytest.approx(50 / 120)
