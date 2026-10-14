"""Original soft major-key music: warm plucks and low piano tones, no bell treble."""
from pathlib import Path
import wave
import numpy as np

rate, duration = 48000, 30
mix = np.zeros(rate * duration, dtype=np.float64)

def note(midi, start, seconds, level, pluck=False):
    count = int(seconds * rate)
    t = np.arange(count) / rate
    frequency = 440 * 2 ** ((midi - 69) / 12)
    attack = 1 - np.exp(-t / (0.025 if pluck else 0.075))
    release = np.minimum(1, (seconds - t) / 0.3)
    envelope = attack * release * np.exp(-t * (3.8 if pluck else 1.25))
    tone = np.sin(2 * np.pi * frequency * t)
    tone += (0.10 if pluck else 0.05) * np.sin(2 * np.pi * frequency * 2 * t)
    tone += 0.018 * np.sin(2 * np.pi * frequency * 3 * t)
    start_index = int(start * rate)
    count = min(count, len(mix) - start_index)
    if count > 0:
        mix[start_index:start_index + count] += tone[:count] * envelope[:count] * level

beat = 60 / 104
chords = [(48,55,60,64), (45,52,57,60), (41,48,53,57), (43,50,55,59)]
melody = [64,67,69,67,64,62,60,62, 64,67,64,62,60,62,64,60]
for index in range(52):
    start = index * beat
    if start >= duration: break
    chord = chords[(index // 4) % 4]
    if index % 4 == 0: note(chord[0]-12, start, 2*beat, 0.038)
    note(chord[1+(index % 3)], start+0.02, 1.35*beat, 0.025, True)
    if index % 2 == 0:
        note(chord[2], start+beat/2, 0.8*beat, 0.012, True)
    note(melody[index % len(melody)], start+0.055, 1.5*beat, 0.052, True)

# Soft room reflection and a smooth low pass; no percussion hiss or high bell peaks.
echo = int(rate*0.135)
mix[echo:] += mix[:-echo].copy() * 0.11
frequencies = np.fft.rfftfreq(len(mix), 1/rate)
mix = np.fft.irfft(np.fft.rfft(mix) / (1 + (frequencies/1700)**6), n=len(mix))

time = np.arange(len(mix)) / rate
mix *= np.minimum(1, time / 0.7) * np.minimum(1, (duration - time) / 1.7)
right = mix.copy()
delay = int(rate * 0.013)
right[delay:] = 0.92 * mix[delay:] + 0.08 * mix[:-delay]
stereo = np.column_stack((mix, right))
output = Path(__file__).parent / 'assets' / 'original-music.wav'
with wave.open(str(output), 'wb') as audio:
    audio.setnchannels(2)
    audio.setsampwidth(2)
    audio.setframerate(rate)
    audio.writeframes((np.clip(stereo, -1, 1) * 32767).astype('<i2').tobytes())
print(output)
