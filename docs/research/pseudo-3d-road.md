# Pseudo-3D road rendering: track representation and projection

Research for issue #3 (part of map #1). Question: how do classic segment-based pseudo-3D road renderers represent a track (segments, curvature, elevation, width), project it from the driver's eye, push the car outwards on curves, and place and scale roadside objects? Which concepts does a minimal cockpit-view racer need, and which are optional?

## Sources

Primary sources, both written by people who built working renderers:

- **[LOU]** Louis Gorenfeld, *Lou's Pseudo 3d Page*, <https://www.extentofthejam.com/pseudo/>. The page was read from the Wayback Machine snapshot of 2024-12-26 (<https://web.archive.org/web/20241226171739/http://www.extentofthejam.com/pseudo/>) because the live site was blocked on the research machine's network. Citations below name the section heading.
- **[JG-n]** Jake Gordon, the *Javascript Racer* write-ups (four parts). The old `codeincomplete.com` URLs now 301-redirect to these:
  - [JG-1] <https://jakesgordon.com/writing/javascript-racer-v1-straight/>
  - [JG-2] <https://jakesgordon.com/writing/javascript-racer-v2-curves/>
  - [JG-3] <https://jakesgordon.com/writing/javascript-racer-v3-hills/>
  - [JG-4] <https://jakesgordon.com/writing/javascript-racer-v4-final/>
- **[SRC]** The source code behind those write-ups (MIT licence), pinned to commit `3e8a060`:
  - [SRC-v4] <https://github.com/jakesgordon/javascript-racer/blob/3e8a060b5900755db27f899612a74a77427c853e/v4.final.html>
  - [SRC-common] <https://github.com/jakesgordon/javascript-racer/blob/3e8a060b5900755db27f899612a74a77427c853e/common.js>

  Line numbers below (for example `v4:421`) refer to these pinned files. Where a write-up and the code disagree, the code wins.

Claims marked **(inference)** are my own reasoning for this project. No source states them.

---

## 1. The two families of renderer

LOU describes two approaches:

1. **Raster roads.** For each screen scanline you store a value (a precomputed Z distance, a horizontal shift, a colour) and change it line by line. "These are special effects which are done by changing some variable per line" [LOU, *Introduction to Raster Roads*]. Curves come from scrolling each line sideways, and the stripes come from colour cycling or palette changes [LOU, same section].
2. **True 3D-projected segments.** "The track is made of polygonal segments. However, rather than moving in full 3d space, it still only moves towards the camera. For curves, the road still just skews left and right … There is no actual rotation when going around curves" [LOU, *3d-Projected Segments vs. Raster Roads*]. LOU names Road Rash and Test Drive II as games that used it [same section].

The segment approach has two advantages, according to LOU. "Real 3d geometry can be used for the hills", and "Terrain and road width changes don't need to be done using a separate technique". The costs are "more calculations" and "a decent number of segments must be used or the road will look jagged" [LOU, *Pros / Cons* under *True 3d-Projected Segments*]. Jake Gordon's Javascript Racer uses this approach, and LOU sends readers to it for the details [LOU, *Further Reading on 3d-Projected Segments*].

**Recommendation (inference):** use projected segments. They put the track in world units, not screen lines, so the track data does not depend on the output resolution. Hills come from the same projection formula with no separate trick. The maths is a small set of pure functions that are easy to unit-test. In Python, the extra multiplies and divides cost nothing that matters at 256×192.

## 2. Track representation

### 2.1 Segments

- The road is an array of equal-length segments. Each segment has a near point `p1` and a far point `p2`, and its `p2` is the next segment's `p1` [JG-1]. In code, `p1.world.z = n*segmentLength` and `p2.world.z = (n+1)*segmentLength` [SRC-v4 `v4:421-432`].
- A segment stores: `index`, `p1`/`p2` (with `world`, `camera` and `screen` sub-objects), `curve`, `sprites[]`, `cars[]` and `color` [SRC-v4 `v4:423-430`].
- The defaults are `segmentLength = 200`, `roadWidth = 2000` (half the road's width: "the road spans from -roadWidth to +roadWidth"), `lanes = 3`, `rumbleLength = 3` and `drawDistance = 300` segments [SRC-v4 `v4:113-121`].
- Track length is the number of segments × `segmentLength`. The track loops: `findSegment(z)` returns `segments[floor(z/segmentLength) % segments.length]` [JG-1].
- LOU's equivalent: "a road segment is a partition which is invisible to the player … an invisible horizontal divide which sets the curve of the road above that line" [LOU, *Making it Curve*]. In the 3D version, "each segment here still has a curve amount (ddx), and either a hill amount (ddy) or a y-position … these can also have other attributes as well such as terrain changes" [LOU, *The Basic 3d Road*].

### 2.2 Curvature

- Curvature is a single number per segment. It is **not** a heading or an angle: "negative values mean left turns, positive mean right, and larger magnitudes mean tighter bends". The tuned presets are `CURVE: { NONE: 0, EASY: 2, MEDIUM: 4, HARD: 6 }` [JG-2; SRC-v4 `v4:453`].
- The track has no real 2D layout (x/z plan). Gordon calls this a "fake" curve, correct only "as … correct as a 'fake' curve can be" [JG-2]. LOU says the same: "these games do not use a traditional track format with perfect spatial relationships" [LOU, *Why Pseudo 3d?*].
- Curves ease in and out. `addRoad(enter, hold, leave, curve, y)` eases the curve from 0 up to its value over `enter` segments, holds it for `hold` segments, and eases it back to 0 over `leave` segments [JG-2; SRC-v4 `v4:438-448`].

### 2.3 Elevation

- Hills add a world `y` to each segment point. `p1.world.y` is the previous segment's `p2.world.y` (`lastY()`), and `p2.world.y` comes from the builder [JG-3; SRC-v4 `v4:425-426`].
- The same `addRoad` call eases height from `startY` to `endY = startY + y*segmentLength` over the whole enter+hold+leave span. The presets are `HILL: { NONE: 0, LOW: 20, MEDIUM: 40, HIGH: 60 }` [SRC-v4 `v4:438-452`].
- Rendering needed no changes for hills, because the projection was "already set up to project our road segments correctly with non-zero y coordinates" [JG-3].

### 2.4 Width, lanes and colour

- Road width is one global half-width. Rumble strip and lane marker widths are fractions of the projected road width: `rumbleWidth = w/max(6, 2*lanes)` and `laneMarkerWidth = w/max(32, 8*lanes)` [SRC-common `Render.rumbleWidth`/`laneMarkerWidth`].
- Javascript Racer does not vary width per segment. LOU notes that OutRun widened and narrowed its road by overlapping two roads [LOU, *Multiple Roads*], and that in a segment engine width changes fit the same model [LOU, *Pros*].

### 2.5 Building a track: a list of commands

- Gordon builds tracks in code with helpers such as `addStraight(num)`, `addCurve(num, curve, height)`, `addHill(num, height)`, `addSCurves()` and `addLowRollingHills()`. They all expand into `addRoad` calls [SRC-v4 `v4:456-528`]. There are named length presets: `LENGTH: { SHORT: 25, MEDIUM: 50, LONG: 100 }` segments [SRC-v4 `v4:451`].
- LOU stored his first track as "a list of events which would happen at specified distances … commands to begin and stop curves". With segments, "you can just use a list of commands" [LOU, *Storing Track Data*].
- Gordon closes his track by easing the height back to zero (`-lastY()/segmentLength`) so the loop meets itself [SRC-v4 `v4:506`]. Start and finish segments are recoloured with special `START`/`FINISH` colours [SRC-common `COLORS`].

## 3. Projection from the camera

### 3.1 The formula

- By similar triangles, `y_screen/dist = y_world/z_world`, so `y_screen = y_world*dist/z_world`. You then add half the screen resolution to centre the result [LOU, *A Mathematical Detour: 3d Perspective Projection*].
- Field of view sets the scale: `scaling = (x_resolution/2) / tan(fov/2)` [LOU, *More Math: Adding Field-of-View*]. Gordon normalises this to `cameraDepth = 1/tan(fov/2)` with a default `fieldOfView = 100°` [JG-1; SRC-v4 `v4:118, 641`].
- Gordon's projection has three steps: translate to camera space, project, then scale to pixels with Y flipped [JG-1]. The whole function [SRC-common `Util.project`]:

  ```js
  p.camera.x     = (p.world.x || 0) - cameraX;
  p.camera.y     = (p.world.y || 0) - cameraY;
  p.camera.z     = (p.world.z || 0) - cameraZ;
  p.screen.scale = cameraDepth/p.camera.z;
  p.screen.x     = Math.round((width/2)  + (p.screen.scale * p.camera.x  * width/2));
  p.screen.y     = Math.round((height/2) - (p.screen.scale * p.camera.y  * height/2));
  p.screen.w     = Math.round(             (p.screen.scale * roadWidth   * width/2));
  ```

  This is a pure function of a world point plus the camera parameters. It is a natural core-layer unit **(inference)**.

### 3.2 Camera height, position and the car

- `cameraHeight = 1000` world units by default, and the UI lets you adjust it from 500 to 5000 [SRC-v4 `v4:119, 49-50`]. The camera's y each frame is `playerY + cameraHeight`, where `playerY` is interpolated from the world y at both ends of the player's segment. This keeps the camera at a fixed height above the road over hills [SRC-v4 `v4:335, 356`].
- `position` is the **camera's** Z. The car sits `playerZ = cameraHeight * cameraDepth` ahead of it [JG-1; SRC-v4 `v4:643`]. This makes Javascript Racer a chase-camera game: the car sprite is drawn at scale `cameraDepth/playerZ` near the bottom centre of the screen [JG-1; SRC-v4 `v4:401-406`].
- The player's lateral position `playerX` is normalised: −1 is the left edge of the road and +1 the right edge. The camera x is `playerX * roadWidth` [SRC-v4 `v4:356`].
- **For a cockpit view (inference):** put the camera at the driver's eye. That means `playerZ ≈ 0` (the car is where the camera is), a low `cameraHeight` (roughly a seated driver's eye above the road), and a fixed cockpit or HUD graphic drawn over the bottom of the frame instead of a scaled car sprite. With no visible car you need no car scaling, and you need no player-sprite tilt over hills like Gordon's (`v4:406`). LOU's *Perspective-style Steering* argues that steering should move the road, not a sprite, which is what a cockpit view does by nature [LOU].

### 3.3 Z-map (raster alternative)

LOU's raster method precomputes one Z per scanline, `Z = Y_world / (Y_screen - height_screen/2)`, where `Y_world` is the (negative) camera height [LOU, *A More Accurate Road - Using a Z Map*]. That fixes the "oatmeal effect" of naive accumulation, in which stripes "appear to slow down as they move outwards" [LOU, *The Simplest Road*]. The segment approach does not need a Z-map. It is mentioned here only because it is the cheapest correct flat road if hills are dropped **(inference)**.

## 4. Curves: accumulation and the push on the car

### 4.1 Rendering curves

Each segment shifts the road's centre line by an accumulated offset. Points are never rotated [JG-2]:

```js
var x  = 0;
var dx = - (baseSegment.curve * basePercent);   // v4:338-339
...
Util.project(segment.p1, (playerX * roadWidth) - x,      ...);
Util.project(segment.p2, (playerX * roadWidth) - x - dx, ...);
x  = x + dx;
dx = dx + segment.curve;                          // v4:356-360
```

- This is second-order accumulation. `curve` plays the part of LOU's `ddx`, so the road's x is a sum of an arithmetic series, `s = x + A·N(N+1)/2` [LOU, *General Curve Formula*]. LOU's raster pseudocode is the same: `ddx += dx; current_x += ddx` per line [LOU, *Making it Curve*].
- **The start offset matters.** Without `dx = -percent * curve` for the base segment, the road jitters every time the camera crosses a segment boundary. LOU credits Gordon with the fix: `dx = -percentage_of_segment_traversed * ddx` "makes the X of the road a function of its Z" [LOU, *Scrolling the Road*].
- Seeing a straight beyond the curve, or the next bend coming, is a real benefit of segments: "you can see that next piece of track coming around the bend before you hit it" [LOU, *Making it Curve*].
- Background or horizon: the parallax layers scroll by `layerSpeed * playerSegment.curve * distance travelled`, with `sky 0.001`, `hills 0.002` and `trees 0.003` [JG-2; SRC-v4 `v4:99-101, 212-214`]. In LOU's version the horizon "scrolls quickly in the opposite direction that the curve is pointing", taken from the base segment [LOU, *Making it Curve*].

### 4.2 Centrifugal push

A curve pushes the player sideways in proportion to speed and curvature [JG-2; SRC-v4 `v4:158-171`]:

```js
var speedPercent = speed/maxSpeed;
var dx = dt * 2 * speedPercent;   // full-speed steering crosses -1..1 in 1 s
if (keyLeft)  playerX = playerX - dx;
else if (keyRight) playerX = playerX + dx;
playerX = playerX - (dx * speedPercent * playerSegment.curve * centrifugal);  // centrifugal = 0.3
```

- The push grows with speed squared, since `dx` is already proportional to speed. `centrifugal = 0.3` was tuned by feel [JG-2; SRC-v4 `v4:97`].
- LOU does not describe a centrifugal push. His page is about rendering. The push is a gameplay rule, not part of the renderer **(inference)**.

### 4.3 Related physics in the same loop (context for the car model)

- Speed: `maxSpeed = segmentLength/step` ("ensure we can't move more than 1 segment in a single frame"), `accel = maxSpeed/5`, `breaking = -maxSpeed`, `decel = -maxSpeed/5` [SRC-v4 `v4:127-130`].
- Off-road (`|playerX| > 1`) applies `offRoadDecel = -maxSpeed/2` down to a floor of `offRoadLimit = maxSpeed/4` [SRC-v4 `v4:131-132, 181-184`]. `playerX` is clamped to ±3 [SRC-v4 `v4:209`].
- Lap timing: a lap ends when `position` wraps past the start [SRC-v4 `v4:216-231`].

## 5. Hills, clipping and drawing order

- The road is drawn **front to back**. The renderer keeps `maxy`, the screen-y of the last road row drawn, starting at the screen height. It skips a segment if it is behind the camera (`p1.camera.z <= cameraDepth`), back-facing (`p2.screen.y >= p1.screen.y`), or hidden behind a nearer hill (`p2.screen.y >= maxy`) [SRC-v4 `v4:362-365`; JG-1]. After drawing a segment it sets `maxy = p1.screen.y`. (The pinned code uses `p1`. The JG-1 write-up says `p2`.) [SRC-v4 `v4:377`].
- LOU gives the same rule: "From the front of the screen back, a 3d segment whose screen_y is projected as lower than the last-drawn 3d segment would not be shown (however, its sprites may still be visible because they stick up)" [LOU, *The Basic 3d Road*].
- Each segment records `segment.clip = maxy` at the time it is visited. Sprites use it later [SRC-v4 `v4:354`; JG-4].
- LOU's raster alternative, *Faked Hills*, stretches or compresses the Z-map vertically by varying how far the draw position moves per line. It is cheap ("No multiplies or divides necessary"), but "Accurate 3d geometry is impossible" and it needs tweaking [LOU, *Faked Hills*].
- Fog: `exponentialFog(d, density) = 1/e^(d²·density)` over a normalised distance, drawn as a translucent overlay per segment [SRC-common `Util.exponentialFog`, `Render.fog`; SRC-v4 `v4:353`].

## 6. Roadside objects

- **Placement:** each segment has a `sprites[]` list of `{source, offset}` entries. `offset` uses the road's normalised units: −1 is the left edge, +1 the right edge, and values beyond ±1 are off-road [JG-4]. Sprites are placed by segment index, for example `addSprite(20, SPRITES.BILLBOARD07, -1)` [JG-4].
- **Scaling:** a sprite uses the projected scale of its segment's near point. `spriteScale = p1.screen.scale`, `spriteX = p1.screen.x + spriteScale*offset*roadWidth*width/2` and `spriteY = p1.screen.y` [SRC-v4 `v4:392-397`]. Drawn size is `sprite.w * scale * width/2 * (SPRITES.SCALE*roadWidth)` [SRC-common `Render.sprite`]. LOU: keep the object's x relative to the road centre, "multiply it by the scaling factor for the current line (inverse of Z) and add that to the road's center" [LOU, *Placing Objects and Scaling*].
- **Order:** after the road pass, sprites are drawn **back to front** (the painter's algorithm) [SRC-v4 `v4:380-408`; LOU, *Placing Objects and Scaling*].
- **Clipping:** a sprite is cut off at its segment's `clip` line, so it can poke up over a crest while its base stays hidden [JG-4; SRC-v4 `v4:397`]. LOU: draw each sprite line "until it hits the last visible segment's screen Y position … if the top of the sprite is below the last segment's Y position, the sprite won't be visible at all" [LOU, *Placing Sprites*].
- **Collision:** sprites are only checked when off-road (`|playerX| > 1`), against the player's current segment. In the pinned code a hit sets `speed = maxSpeed/5` and puts the car back at the front of the segment [SRC-v4 `v4:181-193`].

## 7. Stripes and speed cues

- Alternating light and dark strips give the "good impression of distance" and the sense of motion [LOU, *The Simplest Road*].
- With segments, colour is fixed per segment: `color = floor(n/rumbleLength) % 2 ? DARK : LIGHT`. With `rumbleLength = 3`, every band is 3 segments long [SRC-v4 `v4:430, 115`]. A segment draws grass, rumble, road and (for LIGHT segments only) lane markers in that segment's colour set [SRC-common `Render.segment`, `COLORS`]. A fine segment grid keeps curves smooth while the colour bands stay long [JG-1].
- In a raster road, the equivalent trick is to let one bit of the per-line Z pick the shade: "For each Z, make one of the bits represent the shade of the road" [LOU, *Texturing the Road*].
- **For a low-colour Spectrum-style look (inference):** only 2 colours per element (grass, rumble, road surface, optional lane line) are needed. The bands come for free from segment parity. You need no textures, fog or palette cycling.

## 8. Essential vs optional for a minimal cockpit-view racer

| Concept | Minimal MVP | Notes |
|---|---|---|
| Fixed-length segments, looping track, `findSegment` | **Essential** | Core data model [JG-1] |
| Per-segment `curve` + second-order x/dx accumulation + base-segment `-percent*curve` correction | **Essential** | Without the correction the road jitters at boundaries [LOU *Scrolling the Road*] |
| Projection (`cameraDepth = 1/tan(fov/2)`, `scale = depth/z`) | **Essential** | Pure function [SRC-common `Util.project`] |
| Camera at the driver's eye, low height, `playerZ ≈ 0`, cockpit overlay | **Essential** for a cockpit view | (inference) from §3.2 |
| Alternating segment colours (rumble, grass, road) | **Essential** | The main speed cue [LOU *The Simplest Road*; SRC-v4 `v4:430`] |
| Front-to-back drawing with behind-camera cull | **Essential** | [SRC-v4 `v4:362`] |
| Centrifugal push `-dx*speed%*curve*k` | **Essential** for gameplay | Without it curves cost no effort [JG-2] |
| Off-road slowdown (`|x|>1`) | **Essential** for gameplay | [SRC-v4 `v4:181-184`] |
| Lap or start-line detection | **Essential** for time trial | [SRC-v4 `v4:216`] |
| Curve easing (enter/hold/leave) | Strongly recommended | Can be applied when the track loads (§9) [SRC-v4 `v4:438`] |
| Horizon or background that scrolls with curvature | Strongly recommended | Without it, curves read as "the road bends" rather than "I'm turning" [LOU *Making it Curve*] |
| Hills (world y) + `maxy` hill clipping | Optional | Cheap to add later, since projection already handles y [JG-3]. Clipping is only needed if hills exist |
| Roadside sprites (placement, scaling, clip, painter's order) | Optional | Strong extra speed cue, plus a collision rule [JG-4] |
| Sprite collision | Optional | Only relevant with roadside sprites |
| Lane markers | Optional | |
| Fog | Optional | Hard to do in a palette of few colours (inference) |
| Variable road width, forks, multiple roads | Out of scope | [LOU *Multiple Roads*] |
| Other cars (AI) | Out of scope | Lone driver against the clock |

## 9. Implications for circuit data

**(inference throughout, building on §2.5)**

- The natural authoring unit is a **section**, not a segment: `{length, curve, hill?}` with enter/hold/leave easing, as in `addRoad(enter, hold, leave, curve, y)` [SRC-v4 `v4:438`] or LOU's "list of commands" [LOU, *Storing Track Data*]. A circuit file (TOML, JSON or Python data) is then an ordered list of sections plus a few global properties: road half-width, segment length, rumble length, lanes, colour scheme, start or finish segment, and roadside sprite placements as `(segment index or distance, sprite id, offset)`.
- A pure loader expands sections into a flat `list[Segment]`. That expansion is deterministic and easy to test: segment count = sum of lengths, the curve is 0 at section ends, and the height returns to its start value on a closed loop.
- Curvature is dimensionless and tuned by feel (presets 2/4/6). The track has no real plan geometry, so you cannot draw an accurate overhead circuit map from the same data, and you cannot check that a loop "closes" in x/z. If a minimap or a real-world-shaped circuit matters, it needs separate data or a different curve model.
- Keep the units in world units (segment length, road width, height in multiples of segment length), never in pixels. Then circuits do not change when the internal resolution (~256×192) or FOV is tuned.
- Defaults to start tuning from: Gordon's values are tuned for 1024×768. A 256×192 render needs far fewer segments drawn before they shrink below a pixel. `drawDistance` and `segmentLength` should be tuned, not copied.

## 10. Implications for a pure, testable core

**(inference)**

- **Domain or core (pure, no pygame):** `Segment` and `Track` value objects; the section → segment builder with easing; `find_segment(z)` with wrap-around; `project(point, camera, screen) -> ScreenPoint`; and a `RoadFrame` function that takes `(track, camera position, player x, screen size)` and returns the list of visible, projected road quads with colours and clip lines, plus the list of projected sprites in back-to-front order. Also the car update `(state, input, segment, dt) -> state`, which covers steering, centrifugal push, speed, off-road and lap crossing.
- **Adapter (pygame):** only fills polygons and blits sprites from that list, at 256×192, then scales the surface up.
- Everything Gordon's `render()` does except the `ctx.*` calls is arithmetic over segments [SRC-v4 `v4:329-408`]. You can split it cleanly into "compute frame" and "draw frame", which suits Clean Architecture and makes golden or property tests possible. Examples: on a straight flat road every quad is centred; a quad's screen y rises as z grows; nothing beyond `drawDistance` is emitted; a hill crest hides the segments behind it.
- Keep a fixed time step in the update (Gordon uses `step = 1/60` and caps `maxSpeed` at one segment per frame [SRC-v4 `v4:93-94, 127`]). That makes the physics deterministic and testable.

## Open questions this raises for the map

- **Hills in or out of the MVP?** They are cheap with projected segments (the projection already handles y, and clipping is a few lines), but they add `maxy` clipping, camera-y interpolation and horizon handling. For a Spectrum feel, flat circuits are authentic and simpler.
- **Roadside scenery?** Sprites add a strong speed and depth cue and a collision rule. Leaving them out leaves only stripes to give a sense of speed.
- **Horizon or background:** a scrolling horizon is close to essential for curves to read as turning. It needs art and a scroll rule.
- **Circuit format:** a list of sections (length, curve, optional hill) plus sprite placements, expanded at load time. The format should be settled before the three MVP circuits are written.
- **No true plan geometry:** if circuits should resemble real places or show a minimap, the "fake curve" model alone is not enough.
- **Cockpit vs chase camera:** this changes `playerZ`, the camera height and whether a car sprite exists.
