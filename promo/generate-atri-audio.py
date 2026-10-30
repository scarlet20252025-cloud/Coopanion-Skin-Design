"""Synthesize an original underwater-themed background score for the ATRI film.

无第三方采样，全部由正弦/三角波叠加与包络生成；风格对应角色设定（深海、清澈、
高性能少女），比龙娘那支更慢、更空旷，用长衰减与轻微失谐做"水下"质感。

用法:
    python promo/generate-atri-audio.py            # 默认 30 秒
    python promo/generate-atri-audio.py --duration 30 --out promo/assets/atri-music.wav
"""
from pathlib import Path
import argparse
import math
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# A 大调五声：A B C# E F#，避免半音摩擦，配合水下空旷感
SCALE = {
    "A2": 110.00, "E3": 164.81, "A3": 220.00, "B3": 246.94, "C#4": 277.18,
    "E4": 329.63, "F#4": 369.99, "A4": 440.00, "B4": 493.88, "C#5": 554.37,
    "E5": 659.25, "F#5": 739.99, "A5": 880.00,
}

BPM = 92.0
BEAT = 60.0 / BPM


def env_ad(n, attack, decay, sr=SR):
    """线性起音 + 指数衰减，避免任何爆音。"""
    out = [0.0] * n
    a = max(1, int(attack * sr))
    d = max(1, int(decay * sr))
    for i in range(n):
        if i < a:
            out[i] = i / a
        else:
            k = (i - a) / d
            out[i] = math.exp(-3.2 * k)
    return out


def tone(freq, dur, amp, attack=0.02, decay=None, detune=0.0, harmonics=(1.0, 0.32, 0.14, 0.06)):
    """单个音符：基频 + 泛音 + 轻微失谐副音，模拟钢琴/水铃。"""
    n = int(dur * SR)
    decay = decay if decay is not None else dur * 0.75
    e = env_ad(n, attack, decay)
    buf = [0.0] * n
    for h, hg in enumerate(harmonics, start=1):
        if hg <= 0:
            continue
        f = freq * h
        if f > SR * 0.45:
            continue
        w = 2 * math.pi * f / SR
        for i in range(n):
            buf[i] += hg * math.sin(w * i)
    if detune:
        f = freq * (1 + detune)
        w = 2 * math.pi * f / SR
        for i in range(n):
            buf[i] += 0.45 * math.sin(w * i)
    peak = max(1e-9, max(abs(v) for v in buf))
    return [v / peak * amp * e[i] for i, v in enumerate(buf)]


def bed_noise(n, amp, seed=7):
    """极低频水压床：不是白噪声，而是几条缓慢起伏的正弦叠加。"""
    out = [0.0] * n
    comps = [(41.2, 0.5), (55.0, 0.35), (73.4, 0.22), (98.0, 0.12)]
    for f, g in comps:
        w = 2 * math.pi * f / SR
        for i in range(n):
            out[i] += g * math.sin(w * i + seed)
    peak = max(1e-9, max(abs(v) for v in out))
    return [v / peak * amp for v in out]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--duration", type=float, default=30.0)
    ap.add_argument("--out", default="promo/assets/atri-music.wav")
    args = ap.parse_args()

    total = int(args.duration * SR)
    mixbuf = [0.0] * total

    def add(samples, at_sec, gain=1.0):
        start = int(at_sec * SR)
        for i, v in enumerate(samples):
            j = start + i
            if 0 <= j < total:
                mixbuf[j] += v * gain

    # 低频水压床，全程铺底
    add(bed_noise(total, 0.30), 0.0, 1.0)

    # 主旋律：每 2 拍一个音，尾部留白，越到后面越疏
    # (拍位, 音名, 时值秒, 音量)
    melody = [
        (0, "A4", 1.6, 0.42), (2, "C#5", 1.4, 0.36), (4, "E5", 1.8, 0.40),
        (6, "C#5", 1.2, 0.30), (8, "B4", 1.6, 0.34), (10, "A4", 1.8, 0.32),
        (12, "F#4", 1.5, 0.30), (14, "A4", 1.6, 0.34), (16, "E5", 1.9, 0.42),
        (18, "F#5", 1.5, 0.36), (20, "E5", 1.7, 0.34), (22, "C#5", 1.6, 0.32),
        (24, "B4", 1.5, 0.30), (26, "A4", 2.4, 0.38), (28, "E4", 2.6, 0.28),
        (30, "A4", 3.0, 0.34), (32, "A5", 2.6, 0.30),
    ]
    for beat, name, dur, amp in melody:
        t = beat * BEAT
        if t >= args.duration - 0.2:
            continue
        add(tone(SCALE[name], dur, amp, attack=0.018, decay=dur * 0.8, detune=0.0016), t)

    # 低音：每 4 拍一个根音，只有基频与二次泛音，稳住底盘
    bass = [(0, "A2"), (4, "A2"), (8, "E3"), (12, "F#4"), (16, "A2"),
            (20, "C#4" if "C#4" in SCALE else "A3"), (24, "E3"), (28, "A2"), (32, "A2")]
    for beat, name in bass:
        t = beat * BEAT
        if t >= args.duration - 0.2:
            continue
        add(tone(SCALE[name] / 2 if SCALE[name] > 150 else SCALE[name], 2.2, 0.24,
                 attack=0.05, decay=1.6, harmonics=(1.0, 0.12, 0.0, 0.0)), t)

    # 高音点缀：稀疏的水滴感，只在段落切换处出现，避免喧宾夺主
    sparkles = [(3.0, "E5"), (7.4, "B4"), (13.2, "A5"), (19.0, "F#5"), (25.4, "E5"), (28.6, "A5")]
    for t, name in sparkles:
        if t >= args.duration - 0.4:
            continue
        add(tone(SCALE[name] * 2, 0.9, 0.10, attack=0.004, decay=0.55,
                 harmonics=(1.0, 0.2, 0.0, 0.0)), t)

    # 整体淡入淡出，首尾各 0.8 / 2.2 秒，保证首帧与尾帧无突变
    fade_in = int(0.8 * SR)
    fade_out = int(2.2 * SR)
    for i in range(fade_in):
        mixbuf[i] *= i / fade_in
    for i in range(fade_out):
        j = total - 1 - i
        if 0 <= j < total:
            mixbuf[j] *= i / fade_out

    # 归一化到 -1..1 的 0.72，留编解码余量
    peak = max(1e-9, max(abs(v) for v in mixbuf))
    scale = 0.72 / peak

    out = (ROOT / args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for v in mixbuf:
            s = max(-1.0, min(1.0, v * scale))
            frames += struct.pack("<h", int(s * 32767))
        w.writeframes(bytes(frames))

    rms = math.sqrt(sum((v * scale) ** 2 for v in mixbuf[::97]) / max(1, len(mixbuf[::97])))
    print(f"wrote {out}")
    print(f"duration={args.duration}s  sr={SR}  peak_scale={scale:.4f}  rms={rms:.4f}")


if __name__ == "__main__":
    main()
