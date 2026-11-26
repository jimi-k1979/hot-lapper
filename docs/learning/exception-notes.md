# Exception notes

Since Python 3.11, any exception can carry extra lines of context, added with `add_note`. They go into a list on `error.__notes__` and are printed under the message in the traceback:

```python
try:
    return _circuit(stem, _read(path))
except CircuitDataError as error:
    error.add_note(f"in circuit file {path.name}")
    raise
```

A bare `raise` re-raises the *same* exception, so its type, message and original traceback are kept, now with the note.

```
hotlapper.domain.circuit.CircuitDataError: hazards[2].across: is not wholly on the road
in circuit file riverside.toml
```

## Why here

Every bad circuit must stop the game with one `CircuitDataError` naming the file and the field. The domain knows the field but has never heard of files, and it shouldn't. The loader knows the file. So the domain raises the error with the field, and the loader adds the file as a note on the way out. That covers both its own shape errors and the domain's rule errors, without wrapping one exception in another.

## In the code

- [`domain/circuit.py`](../../src/hotlapper/domain/circuit.py): `CircuitDataError`
- [`adapters/circuit_loader.py`](../../src/hotlapper/adapters/circuit_loader.py): `load_circuit`
