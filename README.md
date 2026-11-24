# Hot Lapper

An original cockpit-view, single-seater racing game in Python, built following Clean Architecture. You race alone against the clock on three circuits in one of three cars.

It is influenced by Psion's *Chequered Flag* for the ZX Spectrum, but it is not a port: the circuits, cars, art, text and tuning are all new.

## Development

You need [uv](https://docs.astral.sh/uv/). `make check` runs every quality gate: ruff lint and format checks, mypy, import-linter and pytest. `make fmt` fixes formatting and lint issues that ruff can fix by itself. `make lint` and `make test` run the gates in two halves.

## Credits

One of the circuits is inspired by Silverstone's 1987–90 Grand Prix layout with the Bridge chicane. Its corners carry fictional names.
