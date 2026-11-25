# Constructor injection and the composition root

An object that needs a collaborator takes it as a constructor argument, instead of creating it or reaching for a global:

```python
class Game:
    def __init__(self, clock: Clock, keyboard: Keyboard, renderer: Renderer) -> None:
```

`Game` knows only the protocols. It never learns whether it is talking to pygame or to a test fake.

The real objects are built in exactly one place, the **composition root**:

```python
def main() -> None:
    with PygameDisplay() as display:
        Game(PerfCounterClock(), PygameKeyboard(), display).run()
```

There is no framework or container. Wiring by hand in one place is enough for a game this size, and you can read the whole object graph at a glance.

## Why here

The tests build the same `Game` with a `FakeClock`, a `ScriptedKeyboard` and a `RecordingRenderer`. That runs the real loop headlessly, with time moving only when the test calls `clock.advance(...)`. Only `__main__` constructs the adapters and hands them to the application. import-linter's layers contract keeps the arrows pointing inwards: the application can never import an adapter.

## In the code

- [`application/loop.py`](../../src/hotlapper/application/loop.py): `Game.__init__`
- [`__main__.py`](../../src/hotlapper/__main__.py): the composition root
- [`tests/test_game_loop.py`](../../tests/test_game_loop.py): the `game` fixture
