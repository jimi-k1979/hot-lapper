# /// script
# requires-python = ">=3.13"
# dependencies = ["pygame-ce>=2.5,<2.6"]
# ///
"""PROTOTYPE, throwaway. Never merged.

Answers: which pygame-ce route gives a glitch-free engine note,
the _sdl2 AudioDevice callback or Channel.queue chunks? (ticket #13)

Run:  uv run prototypes/engine_note_spike.py
Starts in the callback route, sounding at idle.

Keys
  1 / 2 / 0   callback route / queue route / silence
  I (hold)    accelerate        K (hold)  brake
  L / J       gear up (revs drop) / gear down (revs jump)
  S           auto sweep on/off  V  voice: engine / pure sine
  [ / ]       smaller / larger buffer (callback) or chunk (queue)
  H           cycle CPU load in the main loop (none / 10 ms / 25 ms)
  Esc         quit
"""

import math
import time
from array import array

import pygame
from pygame._sdl2.audio import AUDIO_F32, AudioDevice

RATE = 44100
MIXER_BUFFER = 512
SIZES = (256, 512, 1024, 2048)
LOADS_MS = (0, 10, 25)
IDLE_HZ = 66.0
MAX_HZ = 600.0
VOLUME = 0.6
TAU = 2 * math.pi


class Voice:
    def __init__(self) -> None:
        self.phase = 0.0
        self.freq = IDLE_HZ
        self.engine = True

    def render(self, n: int, target_hz: float) -> list[float]:
        out = []
        f0 = self.freq
        step = (target_hz - f0) / n
        ph = self.phase
        engine = self.engine
        for i in range(n):
            ph += TAU * (f0 + step * i) / RATE
            if ph >= 2 * TAU:
                ph -= 2 * TAU
            if engine:
                s = 0.35 * (
                    math.sin(ph)
                    + 0.5 * math.sin(2 * ph)
                    + 0.33 * math.sin(3 * ph)
                    + 0.3 * math.sin(ph / 2)
                )
            else:
                s = 0.6 * math.sin(ph)
            out.append(s * VOLUME)
        self.phase = ph
        self.freq = target_hz
        return out


class Stats:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.callbacks = 0
        self.last_cb = 0.0
        self.max_gap_ms = 0.0
        self.late = 0
        self.max_cb_ms = 0.0
        self.starved = 0
        self.queued = 0
        self.errors = ""


voice = Voice()
stats = Stats()
revs = 0.0


def target_hz() -> float:
    return IDLE_HZ + (MAX_HZ - IDLE_HZ) * revs


def callback(_device: object, mv: memoryview) -> None:
    started = time.perf_counter()
    try:
        n = len(mv) // 4
        mv[:] = array("f", voice.render(n, target_hz())).tobytes()
    except Exception as exc:  # noqa: BLE001
        stats.errors = repr(exc)
    now = time.perf_counter()
    if stats.last_cb:
        gap = (started - stats.last_cb) * 1000
        stats.max_gap_ms = max(stats.max_gap_ms, gap)
        if gap > 2 * 1000 * n / RATE:
            stats.late += 1
    stats.last_cb = started
    stats.callbacks += 1
    stats.max_cb_ms = max(stats.max_cb_ms, (now - started) * 1000)


def open_device(size: int) -> AudioDevice:
    device = AudioDevice(
        devicename=None,
        iscapture=False,
        frequency=RATE,
        audioformat=AUDIO_F32,
        numchannels=1,
        chunksize=size,
        allowed_changes=0,
        callback=callback,
    )
    return device


def make_sound(n: int) -> pygame.mixer.Sound:
    samples = voice.render(n, target_hz())
    pcm = array("h", (int(s * 32767) for s in samples))
    return pygame.mixer.Sound(buffer=pcm.tobytes())


def busy(ms: int) -> None:
    end = time.perf_counter() + ms / 1000
    while time.perf_counter() < end:
        pass


def main() -> None:
    global revs
    pygame.mixer.pre_init(RATE, -16, 1, MIXER_BUFFER)
    pygame.init()
    screen = pygame.display.set_mode((256, 192), pygame.SCALED)
    pygame.display.set_caption("PROTOTYPE engine note spike")
    font = pygame.font.Font(None, 16)
    clock = pygame.Clock()
    channel = pygame.mixer.Channel(0)

    mode = "callback"
    size_index = 1
    load_index = 0
    sweep = False
    sweep_t = 0.0
    device: AudioDevice | None = open_device(SIZES[size_index])
    device.pause(0)
    queue_started = False

    def stop_all() -> None:
        nonlocal device, queue_started
        if device is not None:
            device.pause(1)
            device = None
        channel.stop()
        queue_started = False

    running = True
    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        running = False
                    case pygame.K_1:
                        stop_all()
                        stats.reset()
                        mode = "callback"
                        device = open_device(SIZES[size_index])
                        device.pause(0)
                    case pygame.K_2:
                        stop_all()
                        stats.reset()
                        mode = "queue"
                    case pygame.K_0:
                        stop_all()
                        mode = "silence"
                    case pygame.K_l:
                        revs = max(0.0, revs - 0.35)
                    case pygame.K_j:
                        revs = min(1.0, revs + 0.25)
                    case pygame.K_s:
                        sweep = not sweep
                        sweep_t = 0.0
                    case pygame.K_v:
                        voice.engine = not voice.engine
                    case pygame.K_h:
                        load_index = (load_index + 1) % len(LOADS_MS)
                    case pygame.K_LEFTBRACKET | pygame.K_RIGHTBRACKET:
                        delta = 1 if event.key == pygame.K_RIGHTBRACKET else -1
                        size_index = max(0, min(len(SIZES) - 1, size_index + delta))
                        stats.reset()
                        if mode == "callback":
                            stop_all()
                            device = open_device(SIZES[size_index])
                            device.pause(0)

        keys = pygame.key.get_pressed()
        if sweep:
            sweep_t += dt
            revs = 1 - abs((sweep_t / 2) % 2 - 1)
        elif keys[pygame.K_i]:
            revs = min(1.0, revs + 0.6 * dt)
        elif keys[pygame.K_k]:
            revs = max(0.0, revs - 1.0 * dt)
        else:
            revs = max(0.0, revs - 0.3 * dt)

        size = SIZES[size_index]
        if mode == "queue":
            if not channel.get_busy():
                if queue_started:
                    stats.starved += 1
                channel.play(make_sound(size))
                queue_started = True
            if channel.get_queue() is None:
                channel.queue(make_sound(size))
                stats.queued += 1

        busy(LOADS_MS[load_index])

        if mode == "callback":
            latency = size / RATE * 1000
        elif mode == "queue":
            latency = (1.5 * size + MIXER_BUFFER) / RATE * 1000
        else:
            latency = 0.0
        lines = [
            f"mode {mode}   voice {'engine' if voice.engine else 'sine'}",
            f"revs {revs:4.2f}  {target_hz():5.1f} Hz  sweep {'on' if sweep else 'off'}",
            f"size {size} ({size / RATE * 1000:.1f} ms)  ~lat {latency:.0f} ms",
            f"load {LOADS_MS[load_index]} ms  fps {clock.get_fps():4.1f}",
            "",
            f"callbacks {stats.callbacks}  late {stats.late}",
            f"max gap {stats.max_gap_ms:.1f} ms  max cb {stats.max_cb_ms:.2f} ms",
            f"queued {stats.queued}  starved {stats.starved}",
            stats.errors[:40],
            "",
            "1 cb  2 queue  0 off  I/K  J/L  S  V  [ ]  H",
        ]
        screen.fill((0, 0, 40))
        pygame.draw.rect(screen, (60, 60, 60), (8, 172, 240, 10))
        pygame.draw.rect(screen, (220, 80, 40), (8, 172, int(240 * revs), 10))
        for row, text in enumerate(lines):
            screen.blit(font.render(text, False, (230, 230, 230)), (6, 4 + row * 14))
        pygame.display.flip()

    stop_all()
    pygame.quit()


if __name__ == "__main__":
    main()
