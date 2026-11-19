# The core builds the frame; the renderer only draws

Each frame, the application core projects the road and assembles a complete per-screen `Frame` in canvas coordinates: polygons, scaled sprites, dashboard values and text, with colours as palette indices. The pygame renderer adapter only fills, blits and draws text, and holds nothing but the palette's RGB values. We chose this over the usual pygame approach, where the renderer reads the game state and draws it directly, because pseudo-3D projection is pure arithmetic and is the riskiest code in the game. Keeping it in the core means it can be tested with pytest and Hypothesis without a display, and the adapter stays thin enough for a headless smoke test.

## Consequences

- Anything that appears on screen must first appear in a `Frame` dataclass, so new visuals touch the core before the adapter.
- Canvas size and palette indices are core constants. Changing the look means editing the core, not the adapter.
