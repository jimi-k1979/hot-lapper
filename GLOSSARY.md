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

## Car condition

**Engine wear**:
How worn out the engine is, from new to finished. It is never repaired during a race.
_Avoid_: engine damage, engine health

**Tyre wear**:
How worn the tyres are, from new to finished. Worn tyres grip less.
_Avoid_: tyre damage, tread

**Body damage**:
Harm done to the car's bodywork by hazards. Ordinary driving never causes it.
_Avoid_: damage (on its own), health, HP

**Fuel**:
What is left in the car's tank. Every race starts with a full tank.
_Avoid_: petrol, gas

**Puncture**:
A flat tyre caused by running over glass. A punctured car wobbles from side to side and is held to a low speed until the next pit stop.
_Avoid_: flat, blowout

**Holed fuel tank**:
A fuel tank pierced by rocks, so the car uses fuel faster than normal.
_Avoid_: fuel leak, damaged tank

## Hazards

**Hazard**:
A patch of something on the road that harms the car or its handling when the car runs over it. Every hazard is in a fixed place in its circuit. There are five kinds:
- **Oil**: grip drops sharply.
- **Water**: grip drops a little and the car is slowed.
- **Glass**: causes a puncture.
- **Debris**: wears the tyres and causes body damage.
- **Rocks**: cause a holed fuel tank.
_Avoid_: obstacle, hazard object, pickup

## The road

**Gradient**:
How steeply the road climbs or falls. Uphill, a car gathers speed more slowly and stops more quickly; downhill, the reverse.
_Avoid_: slope, incline, hill angle

**Scenery**:
The things beside a circuit that are there to be seen, not touched. All scenery stands beyond the reach of the car.
_Avoid_: props, roadside objects, decorations

**Corner arrow**:
A board of scenery on the outside of a bend, on the approach, pointing the way the corner turns.
_Avoid_: chevron, warning sign

**Start/finish line**:
The line across the road where every lap begins and ends.
_Avoid_: finish line, timing line

**Grid**:
Ten boxes painted on the road just behind the start/finish line, in staggered pairs.
_Avoid_: starting grid, grid slots

**Pole position**:
The front box of the grid, where the car always starts a race.
_Avoid_: pole, front of the grid

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
The opening of a race: the car is held in pole position with its brakes on while red, red, red and then green lights come on a second apart. The player may rev the engine while held. The race clock starts on green.
_Avoid_: countdown, lights out

**Lateral position**:
How far the car is from the centre line of the road, across its width. Steering changes it; the car itself never turns on screen.
_Avoid_: x, offset, lane

**Off the road**:
The state of a car with one whole tyre width past the edge of the road. Off the road the car is slowed heavily.
_Avoid_: off track, on the grass, offroad

**At the limit**:
The state of a car cornering so fast that the outward push of the corner is close to the most its steering can hold. The tyres squeal while the car is at the limit.
_Avoid_: sliding, skidding, drifting

**Stranded timer**:
How long the car has been off the road without a break. It resets the moment the car is back on the road.
_Avoid_: off-road timer, grass timer

**Pit area**:
A marked stretch of road, on one side, just after the start line, where the car stops for a pit stop. It is part of the road, not beside it.
_Avoid_: pit lane, pits, garage

**Pit stop**:
A halt in the pit area during a race, while the race clock keeps running, to refuel the car and repair it. The more there is to repair, the longer it takes.
_Avoid_: service, repair stop

**Race outcome**:
How a race ended. Every race ends in exactly one of six outcomes:
- **Finished**: every lap was completed.
- **Out of fuel**: the fuel ran out and the car rolled to a stop before the finish.
- **Broken down**: the engine wore out.
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
