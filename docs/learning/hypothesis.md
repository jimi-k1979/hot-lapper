# Hypothesis

An ordinary test checks one example you picked. A *property test* states something that must hold for **every** input, and Hypothesis generates hundreds of inputs to try to break it. When one fails, it *shrinks* it to the simplest input that still fails, and remembers it for the next run.

```python
@given(distance=eighths_of_a_metre, laps=st.integers(-50, 50))
def test_segment_lookup_repeats_every_lap(distance: float, laps: int) -> None:
    later = distance + laps * WINDING.length

    assert WINDING.segment_at(later) == WINDING.segment_at(distance)
```

- `@given` turns the test into a property, with one *strategy* per argument.
- Strategies (`st.integers`, `st.floats` and so on) describe the inputs. `.map` transforms what they make.

## Choosing inputs with care

Hypothesis heads straight for edge cases, such as boundaries and tiny or huge values. Here, distances are drawn as whole eighths of a metre (`integers(...).map(lambda e: e / 8)`). Eighths are exact in binary floating point, so `distance + laps * length` has no rounding error. With arbitrary floats, the property would fail for float reasons rather than because of a bug in `segment_at`. The case that needs a float subtlety, a hair before the line, has its own plain test.

## Why here

Segment lookup has to wrap round the loop for any distance: negative, many laps on, or right on a segment boundary. A few examples can't cover that, but two properties can: lookup repeats every lap, and the segment found always contains the distance.

## Invariants for the projection

Projection arithmetic is easy to get subtly wrong, so it's stated as properties rather than examples. A point at eye height always lands on the horizon. Road below the eye always lands below it. Road further ahead is always nearer the horizon and narrower. Road either side of the camera is mirrored. Hypothesis tries hundreds of cameras, distances and offsets for each.

A whole frame gets the same treatment: for any distance and lateral position on a flat, hilly or curving circuit, each road strip lies wholly above the strip nearer the car. That one property covers drawing near to far and hill clipping together.

## In the code

- [`tests/test_circuit.py`](../../tests/test_circuit.py): `test_segment_lookup_repeats_every_lap` and `test_segment_lookup_finds_the_segment_under_the_distance`
- [`tests/test_road.py`](../../tests/test_road.py): the projection properties, and visible segments wrapping round the loop
- [`tests/test_race_view.py`](../../tests/test_race_view.py): `test_road_strips_run_near_to_far_each_wholly_above_the_last`
