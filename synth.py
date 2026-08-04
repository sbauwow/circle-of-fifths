"""Small dependency-free chord synthesizer used by the desktop audio player."""

from __future__ import annotations

from array import array
import math
import sys


def midi_frequency(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def chord_midi_notes(root_pc: int, pitch_classes: set[int]) -> list[int]:
    """Voice pitch classes upward from the chord root in the third octave."""
    root_midi = 48 + (root_pc % 12)
    intervals = sorted((pitch - root_pc) % 12 for pitch in pitch_classes)
    return [root_midi + interval for interval in intervals]


def synthesize_chord(
    root_pc: int,
    pitch_classes: set[int],
    *,
    sample_rate: int = 44_100,
    duration: float = 0.9,
) -> bytes:
    """Return signed 16-bit mono PCM for a short, gently decaying chord."""
    if not pitch_classes:
        return b""
    if sample_rate <= 0 or duration <= 0:
        raise ValueError("sample_rate and duration must be positive")

    frequencies = [midi_frequency(note) for note in chord_midi_notes(
        root_pc, pitch_classes)]
    frame_count = int(sample_rate * duration)
    samples = array("h")

    for frame in range(frame_count):
        time = frame / sample_rate
        attack = min(1.0, time / 0.012)
        release = min(1.0, max(0.0, duration - time) / 0.08)
        decay = math.exp(-2.2 * time / duration)
        envelope = attack * decay * release

        value = 0.0
        for frequency in frequencies:
            phase = 2.0 * math.pi * frequency * time
            value += (
                math.sin(phase)
                + 0.18 * math.sin(phase * 2.0)
                + 0.06 * math.sin(phase * 3.0)
            )
        value /= len(frequencies)
        samples.append(int(max(-1.0, min(1.0, value * envelope * 0.7)) * 32767))

    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()
