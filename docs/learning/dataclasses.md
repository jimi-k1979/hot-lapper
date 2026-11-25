# Frozen, slotted dataclasses

`@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the class's annotated fields. Two options turn it into a good value type:

- **`frozen=True`**: assigning to a field after construction raises `FrozenInstanceError`. To "change" a value you build a new one, usually with `dataclasses.replace(old, field=new)`. Frozen instances are also hashable.
- **`slots=True`**: the class gets `__slots__` instead of a per-instance `__dict__`. Instances are smaller and faster, and a typo such as `controls.brakes = True` fails instead of quietly adding a new attribute.

```python
@dataclass(frozen=True, slots=True)
class Controls:
    accelerate: bool = False
    brake: bool = False
    commands: tuple[Command, ...] = ()
```

Fields that hold collections use `tuple`, not `list`, so the value is immutable all the way down.

## Why here

A `Controls` snapshot is shared by every fixed step in a tick, and a `Frame` is handed from the core to the renderer. If either could be changed in place, one part of the game could change what another part sees. Being frozen rules that out, and `==` comparisons make the tests read naturally (`assert renderer.frames == [TitleFrame(...)]`).

The loop uses `replace` to clear the edge commands after the first step: `replace(controls, commands=())`.

## In the code

- [`domain/controls.py`](../../src/hotlapper/domain/controls.py): `Controls`
- [`domain/frame.py`](../../src/hotlapper/domain/frame.py): `Text` and `TitleFrame`
- [`application/screens.py`](../../src/hotlapper/application/screens.py): the `Title` screen state
- [`application/loop.py`](../../src/hotlapper/application/loop.py): `replace`
