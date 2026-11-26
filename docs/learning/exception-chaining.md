# Exception chaining

Raising a new exception inside an `except` block links it to the one being handled. `from` says how:

```python
except tomllib.TOMLDecodeError as error:
    raise CircuitDataError("syntax", str(error)) from error
```

`from error` *chains* them on purpose: the new exception keeps the original on its `__cause__`, and the traceback shows both, joined by "The above exception was the direct cause of the following exception". Use it when the original still helps someone debugging.

```python
except CircuitDataError as error:
    raise error.in_file(path.name) from None
```

`from None` cuts the link, so the traceback shows only the new exception. Use it when the new one says everything the old one did, and showing both would just be noise.

## Why here

Every bad circuit must stop the game with one `CircuitDataError` naming the file and the field. The domain knows the field but has never heard of files, and it shouldn't. The loader knows the file. So the domain raises the error with the field, and the loader catches it and raises a copy with the file added (`in_file`). The copy says everything the original did, so `from None` keeps the traceback down to one clear error. A TOML syntax error is different. The decoder's own exception has details worth keeping, so it is chained `from error`.

## In the code

- [`domain/circuit.py`](../../src/hotlapper/domain/circuit.py): `CircuitDataError` and `in_file`
- [`adapters/circuit_loader.py`](../../src/hotlapper/adapters/circuit_loader.py): `load_circuit` and `_read`
