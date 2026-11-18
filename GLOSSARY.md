# Glossary

Domain language for **Hot Lapper** (working title), a cockpit-view single-seater racing game.

## Cars

**Car**:
One of the three vehicles a player can choose before a race. Every car is defined by its transmission, its pace and its durability.
_Avoid_: vehicle, model

**Car roster**:
The fixed set of three cars: a robust, slower car with an automatic transmission; a balanced car with a manual transmission; and a fragile, faster, more advanced car with a manual transmission.
_Avoid_: garage, lineup

**Transmission**:
Whether the player changes gear (manual) or the car does it for them (automatic).
_Avoid_: gearbox type

## Racing

**Race**:
A single player driving a chosen car for a chosen number of laps of a chosen circuit, against the clock. There are no other cars on track.
_Avoid_: game, session, run

**Circuit**:
A closed track a race is held on. Some circuits are original designs and some are based on real-world tracks.
_Avoid_: track, course, level

**Circuit map**:
A drawing of a circuit's layout, shown when choosing a circuit. It is an idealised picture; the road actually raced only approximates it.
_Avoid_: track map, minimap

**Lap count**:
How many laps a race lasts, chosen by the player before the race.
_Avoid_: race length, distance

**Race outcome**:
How a race ended. Every race ends in exactly one of six outcomes:
- **Finished**: every lap was completed.
- **Out of fuel**: the fuel ran out and the car rolled to a stop before the finish.
- **Broken down**: a part of the car gave out through wear or reliability.
- **Wrecked**: a hazard damaged the car beyond driving on.
- **Stranded**: the car stayed off the road for too long in one go.
- **Retired**: the player chose to end the race.
_Avoid_: result, ending, DNF

**Retire**:
To end a race by choice before all its laps are done.
_Avoid_: quit, abandon, forfeit

**Best lap**:
The fastest completed lap of a single race. A lap cut short by the race ending does not count.
_Avoid_: fastest lap, PB

**Mechanic's report**:
A short account, in plain sentences, of the state the car is in at the end of a race.
_Avoid_: damage report, diagnostics

**Lap record**:
The fastest single lap ever driven on a circuit, in any car. It is kept between plays.
_Avoid_: high score, best time
