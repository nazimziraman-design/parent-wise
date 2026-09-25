"""Procedural lo-fi track (88 BPM, Am9-Fmaj7-Cmaj7-G6), original and royalty-free.
Usage: python music.py <seconds> <out.wav>"""
import sys, wave
import numpy as np

SR = 44100
CHORDS = [[57, 60, 64, 67, 71], [53, 57, 60, 64], [48, 55, 59, 64], [55, 59, 62, 64]]  # Am9 Fmaj7 Cmaj7 G6
BASS = [45, 41, 36, 43]


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tone(f, d, vol):
    t = np.arange(int(SR * d)) / SR
    env = np.minimum(1, t / 0.03) * np.exp(-t * 2.2)
    return vol * env * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t))


def make(seconds, path):
    rng = np.random.default_rng(7)
    beat = 60 / 88
    n = int(SR * seconds)
    mix = np.zeros(n + SR * 12)
    bar = beat * 4
    for b in range(int(seconds / bar) + 2):
        c, s = b % 4, int(b * bar * SR)
        for m in CHORDS[c]:
            w = tone(hz(m), bar, 0.06)
            mix[s:s + len(w)] += w[:len(mix) - s]
        w = tone(hz(BASS[c]), beat * 2, 0.16)
        mix[s:s + len(w)] += w
        for k in range(4):  # drums
            p = s + int(k * beat * SR)
            if k in (0, 2):
                t = np.arange(int(SR * .18)) / SR
                kick = 0.35 * np.sin(2 * np.pi * (110 - 260 * t) * t) * np.exp(-t * 18)
                mix[p:p + len(kick)] += kick
            if k in (1, 3):
                t = np.arange(int(SR * .12)) / SR
                mix[p:p + len(t)] += 0.10 * rng.standard_normal(len(t)) * np.exp(-t * 30)
            h = np.arange(int(SR * .04)) / SR
            mix[p:p + len(h)] += 0.03 * rng.standard_normal(len(h)) * np.exp(-h * 90)
    mix = mix[:n]
    k = 8
    mix = np.convolve(mix, np.ones(k) / k, mode="same")  # soft lowpass
    fade = min(SR, n // 4)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= max(1e-6, np.abs(mix).max()) / 0.7
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    make(float(sys.argv[1]), sys.argv[2])
