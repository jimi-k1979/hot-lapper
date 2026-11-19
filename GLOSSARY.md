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

**Redline**:
The engine speed above which the engine starts to build heat.
_Avoid_: rev limit, limiter

**Max revs**:
The engine speed at which the engine stops producing power. Changing down at speed can push the engine past it.
_Avoid_: rev limit, limiter

**Engine heat**:
How hot the engine is, from cold to fully overheated. It builds while the engine runs above the redline and cools slowly below it. An automatic car never builds it.
_Avoid_: temperature, overheat level

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

**Start sequence**:
The opening of a race: the car is held on the line with its brakes on while red, red, red and then green lights come on a second apart. The player may rev the engine while held. The race clock starts on green.
_Avoid_: countdown, lights out

**Lateral position**:
How far the car is from the centre line of the road, across its width. Steering changes it; the car itself never turns on screen.
_Avoid_: x, offset, lane

**Off the road**:
The state of a car with one whole tyre width past the edge of the road. Off the road the car is slowed heavily and the warning sound plays.
_Avoid_: off track, on the grass, offroad

**Stranded timer**:
How long the car has been off the road without a break. It resets the moment the car is back on the road.
_Avoid_: off-road timer, grass timer

**Race outcome**:
How a race ended. Every race ends in exactly one of six outcomes:
- **Finished**: every lap was completed.
- **Out of fuel**: the fuel ran out and the car rolled to a stop before the finish.
- **Broken down**: a part of the car gave out through wear or reliability.
- **Wrecked**: a hazard damaged the car beyond driving on.
- **Stranded**: the car stayed off the road for more than 5 seconds in one go.
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
