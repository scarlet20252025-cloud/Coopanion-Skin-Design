"""Synthesize a quiet original piano bed and cues for the desktop film."""
from pathlib import Path
import wave

import numpy as np

RATE = 48000
SECONDS = 35.2
mix = np.zeros((round(RATE * SECONDS), 2), dtype=np.float32)
rng = np.random.default_rng(842)


def add(start, signal, pan=0.0):
    i = round(RATE * start)
    n = min(len(signal), len(mix) - i)
    if n <= 0:
        return
    balance = np.sqrt([.5 - pan / 2, .5 + pan / 2])
    mix[i:i+n] += signal[:n, None] * balance


def piano(start, note, gain, pan=0.0, duration=2.9):
    t = np.arange(round(duration * RATE)) / RATE
    f = 440 * 2 ** ((note - 69) / 12)
    carrier = 2 * np.pi * f * t
    tone = (np.sin(carrier) * np.exp(-t / 1.11)
            + .26 * np.sin(carrier * 2.002 + .15) * np.exp(-t / .58)
            + .085 * np.sin(carrier * 3.005) * np.exp(-t / .23))
    tone *= (1 - np.exp(-t / .009)) * np.minimum((duration - t) * 7, 1) * gain
    add(start, tone, pan)
    add(start + .14, tone * .115, -pan)
    add(start + .27, tone * .06, pan * .7)


def cue(start, duration, gain, frequency, pan=0.0, pitch=0.0, noise=.08):
    t = np.arange(round(duration * RATE)) / RATE
    f = frequency * t + pitch * t * t
    body = np.sin(2 * np.pi * f) + noise * rng.normal(size=t.size)
    shape = (1 - np.exp(-t / .006)) * np.exp(-5 * t / duration)
    add(start, body * shape * gain, pan)


chords = [
    (50, 57, 60, 64, 65, 69, 76),
    (48, 55, 59, 62, 64, 67, 74),
    (46, 53, 57, 60, 62, 65, 72),
    (45, 52, 55, 59, 60, 64, 71),
]
for i in range(12):
    chord = chords[i % len(chords)]
    start = .35 + 2.8 * i
    piano(start, chord[0], .058, -.35)
    piano(start + .06, chord[1], .040, -.27)
    piano(start + .38, chord[3], .036, -.06)
    piano(start + .74, chord[5], .044, .16)
    piano(start + 1.43, chord[4], .033, .16)
    piano(start + 1.84, chord[6], .023, .40)
    if i in (2, 4, 7):
        piano(start + 2.39, chord[5], .026, .32)

for i, event in enumerate([.84, 1.02, 1.20, 1.38, 1.59, 1.81, 2.06, 2.31]):
    cue(event, .13, .025 - .0008 * i, 152 - i * 3, .58 - i * .035, -160, .32)
cue(5.70, .09, .042, 870, -.41, -1850, .30)
cue(6.06, .18, .026, 488, -.38, 170, .025)
for event in (7.73, 8.27, 8.84, 9.46, 10.07):
    cue(event, .19, .012, 174, -.35, 85, .53)
cue(8.33, .38, .021, 515, -.35, 235, .035)
cue(8.47, .40, .017, 628, -.29, 118, .020)
for event in (12.62, 12.86, 13.11, 13.36):
    cue(event, .11, .019, 117, -.24, -100, .24)
cue(18.17, .10, .061, 860, .48, -1900, .30)
cue(18.47, .23, .046, 398, .53, 240, .02)
cue(22.10, .11, .037, 540, .55, -1200, .19)
cue(22.50, .21, .083, 108, .51, -135, .23)
cue(23.63, .36, .021, 638, .38, 160, 0)
cue(28.31, .16, .050, 137, -.31, -175, .22)
cue(30.83, .65, .025, 629, 0, 10, 0)

time = np.arange(len(mix)) / RATE
fade = np.minimum(time / .54, 1) * np.clip((SECONDS - time) / .92, 0, 1)
mix *= fade[:, None] * 2.77
frames = np.rint(np.clip(mix, -.98, .98) * 32767).astype("<i2")
out = Path(__file__).with_name(".capture") / "score.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as audio:
    audio.setparams((2, 2, RATE, len(frames), "NONE", "not compressed"))
    audio.writeframes(frames.tobytes())
