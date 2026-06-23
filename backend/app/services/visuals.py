"""Procedural (no-footage) backgrounds: gradient, solid, audiogram.

Each returns a moviepy clip sized (w, h) lasting `duration`.
"""
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

GRADIENTS = {
    "aurora": [(12, 24, 48), (28, 99, 120), (40, 167, 140)],
    "sunset": [(34, 10, 40), (120, 40, 70), (230, 120, 70)],
    "mint":   [(10, 40, 35), (30, 110, 90), (120, 200, 170)],
    "violet": [(20, 12, 40), (70, 40, 120), (150, 110, 220)],
    "noir":   [(8, 8, 10), (28, 28, 34), (60, 60, 70)],
}


def _hex_rgb(s: str):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _gradient_image(stops, w: int, h: int) -> np.ndarray:
    """Vertical multi-stop gradient, height 2*h so it can scroll."""
    H = h * 2
    ys = np.linspace(0, 1, H)
    seg = np.linspace(0, 1, len(stops))
    cols = np.array(stops, dtype=float)
    r = np.interp(ys, seg, cols[:, 0])
    g = np.interp(ys, seg, cols[:, 1])
    b = np.interp(ys, seg, cols[:, 2])
    col = np.stack([r, g, b], axis=1).astype("uint8")      # (H, 3)
    return np.repeat(col[:, None, :], w, axis=1)            # (H, w, 3)


def gradient_clip(name: str, duration: float, w: int, h: int):
    from moviepy import VideoClip
    img = _gradient_image(GRADIENTS.get(name, GRADIENTS["aurora"]), w, h)
    span = img.shape[0] - h
    def make(t):
        off = int((t / max(duration, 0.1)) * span)         # slow scroll
        return img[off:off + h]
    return VideoClip(make, duration=duration)


def solid_clip(color: str, duration: float, w: int, h: int):
    from moviepy import ColorClip
    return ColorClip(size=(w, h), color=_hex_rgb(color), duration=duration)


def audiogram_clip(audio_path: Path, duration: float, w: int, h: int,
                   color: str = "#28A78C", bg: str = "#0B0E14", bars: int = 56):
    """Frequency-spectrum visualizer (equalizer-style bars) driven by the voice.
    Per frame we FFT a short audio window and map it to log-spaced bands, so the
    bars bounce with the speech instead of sitting at a flat max."""
    from moviepy import VideoClip, AudioFileClip

    sr = 22050
    N = 2048
    a = AudioFileClip(str(audio_path))
    snd = a.to_soundarray(fps=sr)
    a.close()
    if snd.ndim > 1:
        snd = snd.mean(axis=1)

    window = np.hanning(N)
    freqs = np.fft.rfftfreq(N, 1 / sr)
    # log-spaced band edges from ~80 Hz to ~8 kHz
    edges = np.logspace(np.log10(80), np.log10(8000), bars + 1)
    band_idx = [np.where((freqs >= edges[b]) & (freqs < edges[b + 1]))[0] for b in range(bars)]

    fg = np.array(_hex_rgb(color), dtype="uint8")
    bgc = np.array(_hex_rgb(bg), dtype="uint8")
    gap = w / bars
    bar_w = max(3, int(gap * 0.55))
    cy = h // 2
    max_h = int(h * 0.30)

    def make(t):
        frame = np.tile(bgc, (h, w, 1)).astype("uint8")
        c = int(t * sr)
        seg = snd[max(0, c - N // 2): c + N // 2]
        if len(seg) < N:
            seg = np.pad(seg, (0, N - len(seg)))
        mag = np.abs(np.fft.rfft(seg * window))
        vals = np.array([mag[ix].mean() if len(ix) else 0.0 for ix in band_idx])
        vals = np.log1p(vals)
        vals = vals / (vals.max() or 1.0)           # per-frame normalize -> lively equalizer
        for i in range(bars):
            bh = int(max(4, vals[i] * max_h))
            x = int((i + 0.5) * gap) - bar_w // 2
            x0, x1 = max(0, x), min(w, x + bar_w)
            frame[cy - bh:cy + bh, x0:x1] = fg
        return frame

    return VideoClip(make, duration=duration)
