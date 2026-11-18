# Research: which Python game library for Hot Lapper?

Resolves issue #2. Researched 2026-11-18.

**Question.** Which Python 3.13 library best supports: a small fixed canvas (~256x192) scaled up to the window with nearest-neighbour filtering and a limited palette; per-frame keyboard polling plus key events; sound synthesised at runtime (an engine note whose pitch follows the revs, plus simple effects); Linux packaging; and type checking (`mypy --strict`)?

**Candidates.** pygame-ce, pyglet, arcade, and the raylib bindings (`raylib`/`pyray` from raylib-python-cffi; `raylib-py` noted briefly).

## Recommendation

**Use pygame-ce (2.5.x).** Of the four, only pygame-ce provides every one of these in the library itself:

- A real 8-bit palettised `Surface`, so the limited palette is enforced by the library.
- A `SCALED` display mode that scales the window up with nearest-neighbour filtering and integer scale factors.
- `key.get_pressed()`, `get_just_pressed()` and `get_just_released()` for polling, alongside the usual event queue.
- Raw PCM playback through `mixer.Sound(buffer=...)`, plus an SDL audio-device callback for streaming generated samples.
- Bundled, `py.typed` stubs that pass `mypy --strict` with no extra packages.

**Runner-up: raylib (`pyray`).** It has the best API for streamed sound: `LoadAudioStream`, `UpdateAudioStream`, `IsAudioStreamProcessed` and `SetAudioStreamPitch`. It also has render textures with point filtering, and its stubs pass `mypy --strict`. The costs:

- It has no palette concept. You would have to enforce the palette yourself.
- The API is a C-style API full of global state, wrapped through CFFI.
- The project is far smaller, with about 250 GitHub stars against pygame-ce's 1,700.

Pick raylib instead if streamed sound with changing pitch turns out to be the hardest part of the game (see "Open risks" below).

**Not recommended:**

- **pyglet.** Good typed event and polling APIs, and a built-in synthesiser. But you have to build the low-res canvas yourself in OpenGL, and its synthesiser makes fixed-length sounds rather than an endless stream.
- **arcade.** Built on pyglet and adds nothing for synthesised sound. Its last stable release is from October 2025, and it is part-way through a 4.0 development series.

## Comparison

| Criterion | pygame-ce 2.5.8 | pyglet 2.1.19 | arcade 3.3.3 | raylib (pyray) 6.2.0.0 |
|---|---|---|---|---|
| Fixed low-res canvas, nearest-neighbour scaling | `SCALED` flag: nearest filtering, integer scaling when windowed [1][2] | Build your own: render to a texture or framebuffer and set `GL_NEAREST` [8] | `pixelated=True` exists only on the one-time `start_render()` helper, otherwise hand-rolled GL [12] | `LoadRenderTexture` + `SetTextureFilter(POINT)` + `DrawTexturePro` [14] |
| Limited palette | Native 8-bit palettised surfaces (`set_palette`, `set_palette_at`) [3] | None (RGBA only) | None | None (`Color` structs) |
| Keyboard polling | `key.get_pressed`, `get_just_pressed`, `get_just_released` [4] | `KeyStateHandler` [8] | Event callbacks (`on_key_press`); polling through pyglet underneath | `IsKeyDown`, `IsKeyPressed`, queued `GetKeyPressed` [14] |
| Keyboard events | `pygame.event` queue, `KEYDOWN`/`KEYUP`, `set_repeat` [4] | `on_key_press` and similar handlers | `on_key_press` and similar methods | `GetKeyPressed` queue only |
| Playing generated samples | `mixer.Sound(buffer=...)`, `sndarray.make_sound` [5] | Subclass `Source.get_audio_data` [9] | No synthesis API, so drop to pyglet [13] | `UpdateAudioStream` / `IsAudioStreamProcessed` [14] |
| Continuous pitch change | No pitch control in `mixer` [5]. Either change the generated frequency in the `_sdl2.audio.AudioDevice` callback [6], or queue short regenerated chunks with `Channel.queue` [5] | `Player.pitch` (1.0 = normal, 2.0 = one octave up; 0 not allowed) [9] | `play_sound(speed=...)` fixed at start [13] | `SetAudioStreamPitch` (1.0 = normal) [14] |
| Built-in synthesiser | None (generate with numpy or plain Python) | `synthesis`: Sine, Square, Sawtooth, Triangle, WhiteNoise, ADSR and other envelopes; each sound has a fixed `duration` [10][11] | None | None |
| Python 3.13 Linux wheels | cp313 manylinux x86_64, i686, aarch64; classifiers list 3.13 and 3.14 [15] | Pure Python wheel (`py3-none-any`); needs system OpenGL, plus OpenAL or PulseAudio [10][15] | Pure Python wheel; pins `pyglet~=2.1.5`, `pillow~=11.3.0`, `pymunk~=6.9.0` [15] | cp313 manylinux x86_64, i686, aarch64; raylib statically linked [15][16] |
| Latest release / last commit | 2.5.8 (2026-08-09) / 2026-11-15 [15][17] | 2.1.19 (2026-10-11) / 2026-11-17 [15][17] | 3.3.3 (2025-10-09), then `4.0.0.dev6` (2026-08-07) / 2026-10-30 [15][17] | 6.2.0.0 (2026-10-27) / 2026-10-26 [15][17] |
| GitHub stars / open issues | 1,720 / 455 [17] | 2,230 / 42 [17] | 2,107 / 45 [17] | 251 / 16 [17] |
| Typing | `py.typed` + 50 `.pyi` stubs; my test script passes `--strict` [18] | `py.typed`; `--strict` fails on `@window.event` (untyped decorator); `Player.pitch` is `Any` [18] | `py.typed`, inline annotations; passes `--strict` [18] | `py.typed` + generated `__init__.pyi`; passes `--strict`; raw buffers are `Any` / `cffi.FFI` [16][18] |
| Licence | LGPL-2.1 [15] | BSD-3-Clause [15] | MIT [15] | EPL-2.0 [16] |

## Findings in detail

### 1. Low-res canvas, scaling and palette

**pygame-ce.**

- `display.set_mode((256, 192), pygame.SCALED)`:
  - The game sees a 256x192 surface, and "SCALED scales up the window for you" [1].
  - The docs call `SCALED` "an experimental API [that] may change in future releases" [1].
- What the source shows (`src_c/display.c`, tag 2.5.8):
  - `SCALED` creates an SDL renderer.
  - It sets `SDL_HINT_RENDER_SCALE_QUALITY` to `"nearest"`.
  - When windowed, it enables `SDL_RenderSetIntegerScale` ("use whole screen with uneven pixels on fullscreen, exact scale otherwise") [2].
- The same file has a TODO about whether this behaviour is kept under SDL3 [2]. This matters if pygame-ce later moves to SDL3.
- Palette:
  - `Surface((256, 192), depth=8)` with `set_palette(...)` is a true indexed surface [3].
  - "If the Surface is palettized, the pixel color will be set to the most similar color in the palette" [3].
- I verified this headless (SDL dummy drivers, pygame-ce 2.5.8, SDL 2.32.10, Python 3.13.5):
  - `set_mode((256,192), SCALED)` produced a 1024x768 window holding a 256x192 surface.
  - Drawing with palette index 3 read back as index 3 / `(255,255,255)` [18].

**pyglet.** No canvas abstraction. You draw into a texture or `Framebuffer` and scale it with `GL_NEAREST` filtering (`Texture.default_min_filter` / `default_mag_filter`), all in your own OpenGL code [8]. There is no palette support.

**arcade.**

- The only built-in pixelated scaling I found is `start_render(pixelated=False, blend=True)` ("If True, the buffer will be pixelated when resized") [12].
- Its own error text says it is for "a simple script to produce a static image", and it can only be called once [12].
- A game loop would need its own framebuffer plus `arcade.gl` filtering. There is no palette support.

**raylib.**

- The standard pattern [14]:
  - `LoadRenderTexture(256,192)`
  - `SetTextureFilter(tex, TEXTURE_FILTER_POINT)`
  - draw between `BeginTextureMode`/`EndTextureMode`
  - `DrawTexturePro` to the window.
- My `pyray` version of this pattern type-checks under `--strict` [18].
- There is no palette support. Colours are RGBA `Color` structs.

### 2. Keyboard

All four support both polling and events.

**pygame-ce:**

- `get_pressed()`: "a sequence of boolean values representing the state of every key".
- `get_just_pressed()` / `get_just_released()`: "a mapping from key codes to booleans indicating which keys were newly pressed / released". These save writing edge detection.
- `set_repeat` controls repeat delay for `KEYDOWN` events [4].

**raylib:**

- `IsKeyDown` / `IsKeyPressed` for polling.
- `GetKeyPressed()`: "call it multiple times for keys queued, returns 0 when the queue is empty" [14].

**pyglet:** `window.key.KeyStateHandler` for polling, with `on_key_press` events [8].

### 3. Runtime sound synthesis (the main differentiator)

**pygame-ce.**

- `pygame.mixer` has no pitch, playback-rate or streaming-callback API [5]. What it has:
  - `Sound(buffer=...)` copies raw PCM: "The buffer will be copied internally" [5].
  - `Channel.queue` plays one queued Sound "immediately after the current Sound is finished" [5].
  - `set_endevent` posts an event when a sound ends [5].
  - `pre_init(frequency, size, channels, buffer)`, where a smaller buffer lowers latency but "sound dropout may occur" [5].
- Two ways to get a continuously changing engine note:
  - **(a) Callback streaming.** `pygame._sdl2.audio.AudioDevice(..., callback: Callable[[AudioDevice, memoryview], None])` is stubbed and typed in the wheel [6]. SDL calls the callback to fill each audio chunk. Pitch is then just the frequency used in the oscillator's phase step.
    - Verified headless: a 22,050 Hz mono S16 device with 512-frame chunks called the callback 21 times in 0.5 s, about 10,750 frames or roughly real time [18].
    - **Caveat:** `pygame._sdl2` has no page in the pygame-ce reference docs (`docs/reST/ref` lists only `sdl2_video` and `sdl2_controller`) [7]. Its sibling `sdl2_video` page warns "This module isn't ready for prime time yet ... This API will change" [7]. Treat `_sdl2.audio` as experimental.
  - **(b) Chunk queueing.** Generate roughly 20-50 ms buffers at the current revs and keep a `Channel` fed using `queue` and the end event [5]. This uses only stable, documented APIs, but it costs latency and needs care to avoid clicks where chunks join.
- The callback runs on SDL's audio thread and has to take the GIL. On a real device, a pure-Python per-sample loop may need numpy or larger chunks. My test used the dummy driver and did not measure glitches [18].

**pyglet.**

- `media.synthesis` has oscillators and ADSR/tremolo envelopes [10].
- Each `SynthesisSource` is built with a fixed `duration` [11], so it does not stream forever.
- `Player.pitch` changes pitch at runtime ("A pitch of 2.0 will sound one octave higher, and play twice as fast"; 0.0 not permitted) [9].
- For an endless stream you subclass `Source` and implement `get_audio_data(num_bytes)` [9][11]. Of `AudioData` the docs say: "This class is used internally by pyglet" [9].
- On Linux the guide recommends OpenAL over PulseAudio for audio-heavy programs [10].

**arcade.** `load_sound` and `play_sound(..., speed=...)` wrap `pyglet.media` and only play files [13]. Runtime synthesis means using pyglet directly.

**raylib.**

- The C API is designed for streaming [14]:
  - `LoadAudioStream(sampleRate, sampleSize, channels)`
  - poll `IsAudioStreamProcessed` once per frame, then refill with `UpdateAudioStream`
  - `SetAudioStreamPitch` (1.0 = base)
  - `SetAudioStreamBufferSizeDefault`
  - optional `SetAudioStreamCallback` / `AttachAudioStreamProcessor` on the audio thread.
- Polling from the game loop keeps everything on the main thread.
- In `pyray` the data argument is typed `Any`; buffers come from `ffi.new("short[]", n)` [18].

### 4. Packaging and maintenance

From PyPI metadata [15]:

- pygame-ce ships cp313 manylinux wheels for x86_64, i686 and aarch64, and declares 3.13 and 3.14.
- raylib ships cp313 manylinux wheels too. Its README says the Linux binaries "require OS newer than Ubuntu 2016, x64/x86 or Ubuntu 2022 arm64" [16].
- pyglet and arcade are pure Python. pyglet needs system OpenGL and an audio backend (OpenAL `libopenal1` on Debian, or PulseAudio) [10].
- arcade pins `pillow~=11.3.0` and `pymunk~=6.9.0` [15]. Those exact pins could block upgrading those packages later.

Activity [17]:

- pygame-ce, pyglet and raylib-python-cffi all have commits within the last month.
- arcade's last stable release (3.3.3) is 13 months old. A `4.0.0.dev6` tag (2026-08-07) is not on PyPI as a stable release [15][17].
- pygame-ce has many more open issues (455), as you would expect for a larger SDL wrapper. That is not a sign of neglect.

Upstream pygame (not -ce) last released 2.6.1 in September 2024 [15], so pygame-ce is the maintained fork.

### 5. Typing (`mypy --strict`)

I wrote a test script per library that exercises the canvas, keyboard and sound APIs above. I ran mypy 2.4.1 with `--strict` on Python 3.13, against the extracted wheels [18]:

- **pygame-ce:** passes. Types are precise:
  - `get_pressed() -> ScancodeWrapper`
  - `Sound` has overloads for `file` and `buffer: Buffer`
  - `sndarray.make_sound(ndarray) -> Sound`
- **pyray:** passes.
  - `is_key_down(key: int) -> bool`
  - `load_audio_stream(...) -> AudioStream`
  - but `update_audio_stream(..., data: Any, ...)`
- **arcade:** passes. Annotations are inline, e.g. `play_sound(...) -> pyglet.media.player.Player | None`.
- **pyglet:** **fails**: `@window.event` is an untyped decorator (`[untyped-decorator]`). `Player.pitch` shows as `Any`. You can avoid the decorator by subclassing `Window` or using `push_handlers`.

### 6. Keeping it behind a Clean Architecture adapter

The domain needs three ports: a frame sink (an indexed 256x192 pixel buffer), an input source (a set of held keys plus key edges each tick) and a sound sink (a sample generator, or "engine frequency" and "trigger effect" commands).

- **pygame-ce** fits best, because the main loop belongs to the caller:
  - `event.get()`, `key.get_pressed()` and `Clock.tick()` are plain calls [4].
  - An 8-bit `Surface` matches a palette-index frame almost exactly, so the adapter is just "blit the indexed buffer, flip".
  - The audio callback has a pure function signature, `(device, memoryview) -> None` [6]. A domain-side sample generator can be wrapped and unit-tested without SDL.
- **raylib** also leaves the loop to the caller. But it is module-level global state (`init_window`, `begin_drawing`), so the adapter has to own the whole lifecycle.
- **pyglet and arcade** take over the loop: `pyglet.app.run()` and `clock.schedule_interval` call back into handlers, and arcade expects a `Window` subclass. This inverts control, so the adapter becomes the composition root and the domain tick has to be pushed in from a scheduled callback. That works, but it is less natural for a game loop the domain wants to own.

## Trade-offs of the recommendation

- **For pygame-ce:**
  - The only library with native palette surfaces.
  - Nearest-neighbour integer scaling with one flag.
  - The best stubs.
  - Caller-owned loop.
  - Mature and actively maintained.
- **Against pygame-ce:**
  - `SCALED` is labelled experimental [1].
  - Continuous-pitch sound needs either the undocumented `_sdl2.audio` callback [6][7] or chunk queueing with extra latency [5].
  - LGPL-2.1 [15]. This is fine for dynamic linking from a pip wheel, but note it if the game is ever bundled.
  - A future SDL3 migration may change scaling details [2].
- **Mitigation:** keep audio behind a `SoundSink` port, so a raylib or pyglet audio adapter can be swapped in if `_sdl2.audio` proves unstable.

## Open risks / possible new decisions

1. **Sound strategy.** Choose between the `_sdl2.audio` callback (low latency, experimental API) and `Channel.queue` chunks (stable API, more latency). Run a short spike on real hardware (PulseAudio or PipeWire) to measure glitches when a Python callback generates a square wave.
2. **Where the palette lives.** With pygame-ce the palette can be enforced by the surface. If the frame buffer is a domain concept (a numpy or bytes array of indices), the adapter just copies it in with `surfarray` or `pixelcopy`.
3. **Window scale policy.** Windowed `SCALED` gives integer scaling. Fullscreen gives "uneven pixels" (letterboxed but not integer-scaled) [2]. Decide whether fullscreen matters for the MVP.

## Sources

1. pygame-ce docs, `pygame.display` (`SCALED` flag): https://pyga.me/docs/ref/display.html
2. pygame-ce source, `src_c/display.c` @ 2.5.8 (renderer setup, `"nearest"` hint, integer scale): https://github.com/pygame-community/pygame-ce/blob/2.5.8/src_c/display.c
3. pygame-ce docs, `pygame.Surface` (`set_palette`, `set_palette_at`, `set_at` on palettised surfaces): https://pyga.me/docs/ref/surface.html
4. pygame-ce docs, `pygame.key`: https://pyga.me/docs/ref/key.html
5. pygame-ce docs, `pygame.mixer`: https://pyga.me/docs/ref/mixer.html
6. pygame-ce 2.5.8 wheel, `pygame/_sdl2/audio.pyi` (`AudioDevice` callback signature): https://github.com/pygame-community/pygame-ce/blob/2.5.8/buildconfig/stubs/pygame/_sdl2/audio.pyi
7. pygame-ce reference docs directory @ 2.5.8 (no `sdl2_audio` page) and `sdl2_video.rst` warning: https://github.com/pygame-community/pygame-ce/tree/2.5.8/docs/reST/ref
8. pyglet 2.1.19 wheel source (`pyglet.window.key.KeyStateHandler`, `pyglet.image.Texture.default_min_filter`/`default_mag_filter`): https://github.com/pyglet/pyglet
9. pyglet API reference, `pyglet.media` (`Player.pitch`, `Source.get_audio_data`, `AudioData`): https://pyglet.readthedocs.io/en/latest/modules/media.html
10. pyglet programming guide, "Sound and video" (synthesis, Linux audio drivers): https://pyglet.readthedocs.io/en/latest/programming_guide/media.html
11. pyglet source, `pyglet/media/synthesis.py` (`SynthesisSource(generator, duration, sample_rate, envelope)`): https://github.com/pyglet/pyglet/blob/master/pyglet/media/synthesis.py
12. arcade 3.3.3 source, `arcade/window_commands.py` (`start_render(pixelated=...)`): https://github.com/pythonarcade/arcade/blob/3.3.3/arcade/window_commands.py
13. arcade 3.3.3 source, `arcade/sound.py` (built on `pyglet.media`; `load_sound`, `play_sound(speed=...)`): https://github.com/pythonarcade/arcade/blob/3.3.3/arcade/sound.py
14. raylib 6.2 header as shipped in the `raylib` 6.2.0.0 wheel (`raylib.h`: AudioStream, RenderTexture, keyboard functions): https://github.com/raysan5/raylib/blob/master/src/raylib.h, cheatsheet https://www.raylib.com/cheatsheet/cheatsheet.html
15. PyPI JSON metadata (versions, upload dates, wheels, classifiers, licences, `Requires-Dist`): https://pypi.org/project/pygame-ce/ , https://pypi.org/project/pyglet/ , https://pypi.org/project/arcade/ , https://pypi.org/project/raylib/ , https://pypi.org/project/raylib-py/ , https://pypi.org/project/pygame/
16. raylib-python-cffi README (features incl. "Type checking with Mypy", Linux binary requirements, EPL licence, backends): https://github.com/electronstudio/raylib-python-cffi
17. GitHub REST API, repository and release data queried 2026-11-18: `pygame-community/pygame-ce`, `pyglet/pyglet`, `pythonarcade/arcade`, `electronstudio/raylib-python-cffi`, `overdev/raylib-py`
18. Local experiments (2026-11-18, not committed): wheels for each library downloaded from PyPI and extracted; `mypy 2.4.1 --strict` run on one test script per library; headless pygame-ce smoke test (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) of `SCALED`, 8-bit palette and `_sdl2.audio.AudioDevice` callback.

Note on `raylib-py` (overdev): an alternative ctypes binding. Version 6.2.0 is a pure Python wheel requiring Python >=3.12, and its repo had a commit on 2026-10-28 [15][17]. I did not evaluate it in depth. raylib-python-cffi ships compiled CFFI wheels and advertises mypy support [16], which makes it the stronger raylib option here.
