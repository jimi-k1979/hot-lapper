# Generic functions

A generic function has a *type parameter*: a placeholder that mypy fills in at each call. Python 3.12 (PEP 695) lets you declare it in square brackets after the name:

```python
def choice[E: StrEnum](self, key: str, kind: type[E]) -> E:
    ...
    return kind(value)
```

`E: StrEnum` is a *bound*: `E` can be any `StrEnum` subclass and nothing else. Pass `HazardKind` and mypy knows the result is a `HazardKind`. Pass `Side` and it's a `Side`. There's no `TypeVar` to declare at module level, as there was before 3.12.

## Why here

The circuit loader reads four kinds of word from TOML: section kinds, turns and pit sides, hazard kinds and scenery kinds. Each one needs the same checks: it must be a string and it must be one of the enum's values. Without a type parameter you would write four copies, or one function that returns `StrEnum` and needs a cast at every call. With `E`, one function does all four and every result is typed exactly.

## In the code

- [`adapters/circuit_loader.py`](../../src/hotlapper/adapters/circuit_loader.py): `_Table.choice`
