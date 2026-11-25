# Protocols

A `typing.Protocol` describes what an object must be able to do, without saying what it is. Any class with matching methods satisfies the protocol. It doesn't have to inherit from it or even know it exists. This is *structural* typing, checked by mypy rather than at run time.

```python
class Clock(Protocol):
    def now(self) -> Seconds: ...
```

`PerfCounterClock` in the game and `FakeClock` in the tests both have a `now()` method, so mypy accepts either wherever a `Clock` is expected. Neither class mentions `Clock`.

## Why here

The application must not import pygame, but it has to read the time, poll the keyboard and draw. Each of these is a *port*: a protocol the application owns and the adapters satisfy. Abstract base classes (`abc.ABC`) would do the same job, but every adapter would then have to import and inherit from the application's class. With protocols, the adapters and the test fakes are plain classes.

## In the code

- [`application/ports.py`](../../src/hotlapper/application/ports.py): `Clock`, `Keyboard` and `Renderer`
- [`adapters/clock.py`](../../src/hotlapper/adapters/clock.py), [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py) and [`adapters/pygame_keyboard.py`](../../src/hotlapper/adapters/pygame_keyboard.py): the real implementations
- [`tests/fakes.py`](../../tests/fakes.py): the test implementations
