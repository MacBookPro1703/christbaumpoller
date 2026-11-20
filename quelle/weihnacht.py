"""Christbaumpoller – Hintergrundmusik „Feierliche Zufahrt“ (eigene Komposition, Ebbing Project 2026).
Chor-Aah, Schlittenglöckchen, Bläser, Glockenspiel, Pauke. Zitat: „Macht hoch die Tür“ (Melodie Halle 1704, gemeinfrei),
erste zwei Zeilen. Nahtlose Schleife: 16 Takte à 3,0 s = 48 s. Fassung 2 (20.11.2026 23:40): dezenter, Chor führt, Celesta weich, keine Bläser/Pauke, Nachhall wird an den Anfang gefaltet."""
import numpy as np, wave, sys
from scipy.signal import fftconvolve

SR = 44100
BPM = 80
BEAT = 60 / BPM            # 0,75 s
BAR = 4 * BEAT             # 2,5 s
BARS = 16
LOOP = BARS * BAR          # 48 s
TAIL = 5.0
N = int(SR * (LOOP + TAIL))
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(n):
    name, octv = n[:-1], int(n[-1])
    return 440 * 2 ** ((NOTE[name] + 12 * (octv + 1) - 69) / 12)


def add(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    j = min(N, i + len(sig))
    if j <= i:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:j] += sig[: j - i] * gain * l * 1.41
    R[i:j] += sig[: j - i] * gain * r * 1.41


def env_adsr(n, a, d, s, rel, dur):
    t = np.arange(n) / SR
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    e = np.where(t > dur, e * np.exp(-(t - dur) / rel), e)
    return e


# ---------------- Instrumente ----------------
def formant(f):
    """Vokal „a“: Formanten 800/1150/2900 Hz."""
    g = 0.0
    for fc, bw, a in ((700, 0.20, 1.0), (1050, 0.18, 0.55), (500, 0.22, 0.6), (2800, 0.12, 0.12)):
        g += a * np.exp(-((np.log(f / fc)) / bw) ** 2)
    return 0.08 + g


def choir(note, dur, vel=1.0, voices=4):
    f0 = hz(note)
    n = int(SR * (dur + 1.4))
    t = np.arange(n) / SR
    out = np.zeros(n)
    for v in range(voices):
        det = 1 + rng.normal(0, 0.004)
        vib = 1 + 0.006 * np.sin(2 * np.pi * (4.6 + rng.random()) * t + rng.random() * 6)
        ph0 = rng.random() * 6
        f = f0 * det
        k = 1
        while k * f < 4000:
            amp = formant(k * f) / k ** 0.9
            out += amp * np.sin(2 * np.pi * k * f * np.cumsum(vib) / SR + ph0 * k)
            k += 1
    e = env_adsr(n, 0.7, 0.5, 0.9, 1.1, dur)
    return out * e * vel / voices * 0.09


def brass(note, dur, vel=1.0):
    f = hz(note)
    n = int(SR * (dur + 0.6))
    t = np.arange(n) / SR
    e = env_adsr(n, 0.05, 0.15, 0.8, 0.25, dur)
    bright = 2.5 + 9 * np.minimum(1, t / 0.12) * (0.6 + 0.4 * e)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.4)
    ph = 2 * np.pi * f * np.cumsum(vib) / SR
    out = np.zeros(n)
    k = 1
    while k * f < 7000:
        out += np.exp(-k / bright) / k ** 0.3 * np.sin(k * ph)
        k += 1
    return out * e * vel * 0.11


def bell(note, vel=1.0, dec=1.3):
    f = hz(note)
    n = int(SR * 3.0)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 5)
         + 0.06 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t * 9))
    return s * np.exp(-t * dec) * np.minimum(1, t / 0.008) * vel * 0.07


def sleigh(vel=1.0):
    n = int(SR * 0.22)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for _ in range(9):
        f = rng.uniform(3500, 7000)
        d = rng.uniform(0.002, 0.03)
        s += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-np.maximum(0, t - d) * rng.uniform(25, 45)) * (t >= d)
    noise = rng.normal(0, 1, n)
    noise = np.diff(np.concatenate([[0], noise])) * np.exp(-t * 60)
    return (s * 0.5 + noise * 0.06) * vel * 0.018


def bass(note, dur, vel=1.0):
    f = hz(note)
    n = int(SR * (dur + 0.4))
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3)
    return s * np.exp(-t * 1.2) * np.minimum(1, t / 0.03) * vel * 0.14


def timpani(note, vel=1.0):
    f = hz(note)
    n = int(SR * 2.0)
    t = np.arange(n) / SR
    fr = f * (1 + 0.05 * np.exp(-t * 18))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(fr * 1.5) / SR) * np.exp(-t * 3)
    s += rng.normal(0, 1, n) * np.exp(-t * 40) * 0.3
    return s * np.exp(-t * 2.2) * vel * 0.22


# ---------------- Satz ----------------
# Akkorde je Takt (Chor-Lage)
CH = ["C", "Am", "F", "G", "C", "Am", "F", "G", "C/E", "F", "Dm7", "C", "C", "Am", "F", "G7"]
VO = {"C": ["C4", "E4", "G4", "C5"], "Am": ["A3", "E4", "A4", "C5"], "F": ["F3", "C4", "A4", "C5"], "G": ["G3", "D4", "B4", "D5"],
      "C/E": ["E3", "C4", "G4", "C5"], "Dm7": ["D4", "F4", "A4", "C5"], "G7": ["G3", "F4", "B4", "D5"]}
BS = {"C": "C2", "Am": "A1", "F": "F1", "G": "G1", "C/E": "E2", "Dm7": "D2", "G7": "G1"}
# Bläsermelodie (eigene Erfindung), (Note, Start in Schlägen ab Taktbeginn, Dauer in Schlägen)
MEL = {4: [("G4", 0, 1), ("C5", 1, 1), ("E5", 2, 1.5), ("D5", 3.5, 0.5)],
       5: [("C5", 0, 2), ("A4", 2, 1), ("G4", 3, 1)],
       6: [("A4", 0, 1), ("C5", 1, 1), ("F5", 2, 1.5), ("E5", 3.5, 0.5)],
       7: [("D5", 0, 3), ("G4", 3, 1)],
       8: [("E5", 0, 1), ("G5", 1, 1), ("E5", 2, 1), ("C5", 3, 1)],
       9: [("D5", 0, 1.5), ("C5", 1.5, 0.5), ("A4", 2, 2)],
       10: [("F5", 0, 1), ("E5", 1, 1), ("D5", 2, 1), ("B4", 3, 1)],
       11: [("C5", 0, 4)]}
# Zitat „Macht hoch die Tür, die Tor macht weit; es kommt der Herr der Herrlichkeit“ (Halle 1704), C-Dur, Stufen 3 5 4 3 2 1 2 3 | 2 5 4 4 3 3 2 1
ZITAT = [("E5", 0, 1), ("G5", 1, 1), ("F5", 2, 1), ("E5", 3, 1), ("D5", 4, 1), ("C5", 5, 1), ("D5", 6, 1), ("E5", 7, 1),
         ("D5", 8, 1), ("G5", 9, 1), ("F5", 10, 1), ("F5", 11, 1), ("E5", 12, 1), ("E5", 13, 1), ("D5", 14, 2)]

for b, ch in enumerate(CH):
    t0 = b * BAR
    vel = 0.55 + 0.45 * min(1, b / 4)
    for i, nt in enumerate(VO[ch]):
        add(choir(nt, BAR * 0.98, vel), t0, pan=(-0.5 + i / 3) * 0.8)
    if b >= 2:
        add(bass(BS[ch], BEAT * 1.8), t0, 0.0)
        add(bass(BS[ch], BEAT * 1.8, 0.8), t0 + 2 * BEAT, 0.0)

    # Schlittenglöckchen: ab Takt 2 Achtel, ab Takt 5 mit Sechzehntel-Wirbeln
    if 2 <= b <= 14:
        steps = 4 if b < 4 else 8
        for s in range(steps):
            acc = 1.0 if s % (steps // 4) == 0 else 0.5
            add(sleigh(acc * (0.5 if b < 4 else 0.8)), t0 + s * BAR / steps + rng.normal(0, 0.006), pan=0.5)
    # Glockenspiel-Funkeln im Intro und am Ende
    if b < 4 or b >= 12:
        arp = VO[ch][1:] + [VO[ch][-1][:-1] + str(int(VO[ch][-1][-1]) + 1)]
        for i, nt in enumerate(arp):
            o = nt[:-1] + str(int(nt[-1]) + 1)
            add(bell(o, 0.55, dec=0.9), t0 + BEAT * 0.5 * (2 * i + (1 if b % 2 else 0)), pan=-0.4)
for b, notes in MEL.items():
    for nt, st, du in notes:
        add(choir(nt, du * BEAT * 1.02, 1.15, voices=5), b * BAR + st * BEAT, pan=-0.1)
        add(bell(nt[:-1] + str(int(nt[-1]) + 1), 0.25, dec=1.1), b * BAR + st * BEAT, pan=0.3)
# Zitat: Takt 13–16 (Index 12–15), Glockenspiel + Chor-Unisono, darunter leise Bläser
for nt, st, du in ZITAT:
    t = 12 * BAR + st * BEAT
    add(bell(nt, 0.6, dec=0.9), t, pan=0.1)
    add(choir(nt, du * BEAT * 1.02, 1.1, voices=5), t, pan=0.0)
    add(choir(nt[:-1] + str(int(nt[-1]) - 1), du * BEAT * 1.02, 0.6, voices=3), t, pan=-0.2)

# ---------------- Hall (Faltung mit synthetischer Raumantwort) ----------------
rt = np.arange(int(SR * 3.5)) / SR
irL = rng.normal(0, 1, len(rt)) * np.exp(-rt / 0.85)
irR = rng.normal(0, 1, len(rt)) * np.exp(-rt / 0.85)
irL[:int(0.012 * SR)] = 0; irR[:int(0.017 * SR)] = 0
wet = 0.38
L2 = L + wet * fftconvolve(L, irL)[:N] / np.sqrt(np.sum(irL ** 2))
R2 = R + wet * fftconvolve(R, irR)[:N] / np.sqrt(np.sum(irR ** 2))
# Schleife: alles nach 40 s auf den Anfang falten
n = int(LOOP * SR)
outL, outR = L2[:n].copy(), R2[:n].copy()
outL[: N - n] += L2[n:]
outR[: N - n] += R2[n:]
# sanfter Tiefpass (≈6 kHz) gegen Härte, dann weiche Normierung
from scipy.signal import butter, sosfiltfilt
sos = butter(2, 6000, fs=SR, output='sos')
outL, outR = sosfiltfilt(sos, outL), sosfiltfilt(sos, outR)
st = np.stack([outL, outR], 1)
st = np.tanh(st / np.max(np.abs(st)) * 1.2) / np.tanh(1.2) * 0.78
out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/cbp/render/weihnacht.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", out, len(st) / SR, "s")
