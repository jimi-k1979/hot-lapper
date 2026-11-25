# Context managers

A `with` block guarantees that clean-up runs however the block is left: by falling off the end, by `return` or by an exception.

```python
with PygameDisplay() as display:
    Game(..., display).run()
```

Any class with two special methods works:

- `__enter__(self)` runs at the start of the block. Its return value is what `as` binds.
- `__exit__(self, exc_type, exc, traceback)` always runs at the end. The three arguments describe the exception that is propagating, or are all `None`. Returning nothing (`None`) lets any exception carry on.

## `Self`

`__enter__` returns the display itself, and is annotated `-> Self` (from `typing`). `Self` means "an instance of whatever class this method was called on", so a subclass would get its own type back without overriding the annotation.

## Why here

pygame's display must be initialised before the window opens and shut down afterwards, or the window can linger after an error. Putting `pygame.display.init()` in `__enter__` and `pygame.display.quit()` in `__exit__` ties the window's lifetime to the block in `main`. The smoke test checks that the display is shut down once the block ends.

## In the code

- [`adapters/pygame_display.py`](../../src/hotlapper/adapters/pygame_display.py): `PygameDisplay.__enter__` and `__exit__`
- [`__main__.py`](../../src/hotlapper/__main__.py): the `with` block
