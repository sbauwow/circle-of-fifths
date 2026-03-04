"""Music theory engine for Circle of Fifths visualizer.

Pure Python — no Qt dependency. Provides Note, Scale, Chord, Progression,
and GuitarTuning types plus all circle-of-fifths data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Chromatic pitch classes
# ---------------------------------------------------------------------------

CHROMATIC_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CHROMATIC_FLATS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Lookup: name -> pitch class (0-11)
_NAME_TO_PC: dict[str, int] = {}
for _i, _n in enumerate(CHROMATIC_SHARPS):
    _NAME_TO_PC[_n] = _i
for _i, _n in enumerate(CHROMATIC_FLATS):
    _NAME_TO_PC[_n] = _i
# Extra enharmonics
_NAME_TO_PC["Cb"] = 11
_NAME_TO_PC["B#"] = 0
_NAME_TO_PC["E#"] = 5
_NAME_TO_PC["Fb"] = 4

ENHARMONIC = {
    "C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb",
    "Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#",
}

# Letter names in order
LETTERS = ["C", "D", "E", "F", "G", "A", "B"]
LETTER_TO_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

def _spell_note(letter: str, target_pc: int) -> str:
    """Spell a note as letter + accidental to reach the target pitch class."""
    base_pc = LETTER_TO_PC[letter]
    diff = (target_pc - base_pc) % 12
    if diff == 0:
        return letter
    elif diff == 1:
        return letter + "#"
    elif diff == 11:
        return letter + "b"
    elif diff == 2:
        return letter + "##"
    elif diff == 10:
        return letter + "bb"
    # Shouldn't happen for diatonic scales
    return CHROMATIC_SHARPS[target_pc]

# ---------------------------------------------------------------------------
# Note
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Note:
    pitch_class: int  # 0=C .. 11=B
    name: str

    @staticmethod
    def from_name(name: str) -> Note:
        pc = _NAME_TO_PC.get(name)
        if pc is None:
            raise ValueError(f"Unknown note name: {name!r}")
        return Note(pc, name)

    def enharmonic(self) -> Note:
        alt = ENHARMONIC.get(self.name)
        if alt:
            return Note(self.pitch_class, alt)
        return self


# ---------------------------------------------------------------------------
# Circle of Fifths
# ---------------------------------------------------------------------------

# Position index 0-11, clockwise from top (12 o'clock)
CIRCLE_MAJOR_NAMES = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
CIRCLE_MINOR_NAMES = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "Bbm", "Fm", "Cm", "Gm", "Dm"]

# Enharmonic alternatives shown at certain positions
ENHARMONIC_MAJOR = {5: "Cb", 6: "Gb"}  # B/Cb, F#/Gb
ENHARMONIC_MINOR = {5: "Abm", 6: "Ebm"}  # G#m/Abm, D#m/Ebm

# Key signature: position -> (sharps, flats)
KEY_SIGNATURES = {
    0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0), 4: (4, 0), 5: (5, 0),
    6: (6, 6),  # enharmonic pair
    7: (0, 5), 8: (0, 4), 9: (0, 3), 10: (0, 2), 11: (0, 1),
}

# Positions 1-6 are "sharp keys", 7-11 are "flat keys", 0 is natural
def _is_flat_key(position: int) -> bool:
    return position >= 7

def _chromatic_for_position(position: int) -> list[str]:
    return CHROMATIC_FLATS if _is_flat_key(position) else CHROMATIC_SHARPS

def major_name_to_position(name: str) -> int:
    """Return circle position for a major key name."""
    clean = name.replace("m", "") if name.endswith("m") else name
    for i, n in enumerate(CIRCLE_MAJOR_NAMES):
        if n == clean:
            return i
    # Check enharmonic
    for pos, alt in ENHARMONIC_MAJOR.items():
        if alt == clean:
            return pos
    raise ValueError(f"Unknown major key: {name!r}")


# ---------------------------------------------------------------------------
# Modes / Scales
# ---------------------------------------------------------------------------

MODE_INTERVALS: dict[str, list[int]] = {
    "Ionian":     [0, 2, 4, 5, 7, 9, 11],
    "Dorian":     [0, 2, 3, 5, 7, 9, 10],
    "Phrygian":   [0, 1, 3, 5, 7, 8, 10],
    "Lydian":     [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Aeolian":    [0, 2, 3, 5, 7, 8, 10],
    "Locrian":    [0, 1, 3, 5, 6, 8, 10],
}

MODE_NAMES = list(MODE_INTERVALS.keys())

# Scale degree labels relative to root (semitone offset -> label)
DEGREE_LABELS = {
    0: "R", 1: "b2", 2: "2", 3: "b3", 4: "3", 5: "4",
    6: "b5", 7: "5", 8: "b6", 9: "6", 10: "b7", 11: "7",
}


@dataclass
class Scale:
    root: Note
    mode: str
    notes: list[Note]

    @staticmethod
    def build(root_name: str, mode: str) -> Scale:
        root = Note.from_name(root_name)
        intervals = MODE_INTERVALS[mode]

        # Determine root letter (strip accidentals)
        root_letter = root_name[0].upper()
        root_letter_idx = LETTERS.index(root_letter)

        # Build 7 notes: each gets the next letter name, spelled to match
        # the target pitch class
        notes = []
        for step, iv in enumerate(intervals):
            pc = (root.pitch_class + iv) % 12
            letter = LETTERS[(root_letter_idx + step) % 7]
            name = _spell_note(letter, pc)
            notes.append(Note(pc, name))
        return Scale(root, mode, notes)

    @property
    def pitch_classes(self) -> set[int]:
        return {n.pitch_class for n in self.notes}


# ---------------------------------------------------------------------------
# Chords
# ---------------------------------------------------------------------------

# Quality of each diatonic degree in major (Ionian)
_MAJOR_QUALITIES = {
    1: "major", 2: "minor", 3: "minor", 4: "major",
    5: "major", 6: "minor", 7: "dim",
}

_ROMAN_MAJOR = {
    1: "I", 2: "ii", 3: "iii", 4: "IV", 5: "V", 6: "vi", 7: "vii°",
}


@dataclass(frozen=True)
class Chord:
    root: Note
    quality: str
    roman: str
    degree: int


# ---------------------------------------------------------------------------
# Progressions
# ---------------------------------------------------------------------------

# Diatonic degree -> offset in fifths from tonic on the circle
DEGREE_FIFTH_OFFSET = {
    1: 0, 2: 2, 3: 4, 4: -1, 5: 1, 6: 3, 7: 5,
}


def degree_to_circle_position(key_position: int, degree: int) -> int:
    offset = DEGREE_FIFTH_OFFSET.get(degree, 0)
    return (key_position + offset) % 12


@dataclass
class Progression:
    name: str
    degrees: list[int]

    def in_key(self, key_root: str, key_position: int) -> list[Chord]:
        """Return concrete chords for this progression in the given key."""
        scale = Scale.build(key_root, "Ionian")
        chords = []
        for deg in self.degrees:
            d = ((deg - 1) % 7) + 1
            note = scale.notes[d - 1]
            quality = _MAJOR_QUALITIES.get(d, "major")
            roman = _ROMAN_MAJOR.get(d, str(d))
            chords.append(Chord(note, quality, roman, d))
        return chords

    def circle_positions(self, key_position: int) -> list[int]:
        """Return the circle positions for each chord in this progression."""
        return [degree_to_circle_position(key_position, d) for d in self.degrees]


PROGRESSIONS = [
    Progression("I-IV-V-I",    [1, 4, 5, 1]),
    Progression("ii-V-I",      [2, 5, 1]),
    Progression("I-V-vi-IV",   [1, 5, 6, 4]),
    Progression("I-vi-IV-V",   [1, 6, 4, 5]),
    Progression("vi-IV-I-V",   [6, 4, 1, 5]),
    Progression("I-IV-vi-V",   [1, 4, 6, 5]),
    Progression("12-bar blues", [1, 1, 1, 1, 4, 4, 1, 1, 5, 4, 1, 5]),
]


# ---------------------------------------------------------------------------
# Guitar Tunings
# ---------------------------------------------------------------------------

@dataclass
class GuitarTuning:
    name: str
    pitches: list[int]  # MIDI note numbers, 6 strings low-to-high

    @property
    def string_names(self) -> list[str]:
        return [CHROMATIC_SHARPS[p % 12] for p in self.pitches]


TUNINGS = {
    "Standard (EADGBE)":   GuitarTuning("Standard",       [40, 45, 50, 55, 59, 64]),
    "Drop D (DADGBE)":     GuitarTuning("Drop D",         [38, 45, 50, 55, 59, 64]),
    "DADGAD":              GuitarTuning("DADGAD",          [38, 45, 50, 55, 57, 62]),
    "Open G (DGDGBD)":     GuitarTuning("Open G",         [38, 43, 50, 55, 59, 62]),
    "Open D (DADF#AD)":    GuitarTuning("Open D",         [38, 45, 50, 54, 57, 62]),
    "Half Step Down":      GuitarTuning("Eb Standard",    [39, 44, 49, 54, 58, 63]),
    "Open E (EBEG#BE)":    GuitarTuning("Open E",         [40, 47, 52, 56, 59, 64]),
    "Open A (EAEAC#E)":    GuitarTuning("Open A",         [40, 45, 52, 57, 61, 64]),
}

TUNING_NAMES = list(TUNINGS.keys())


def note_at_fret(open_pitch: int, fret: int) -> int:
    """Return pitch class (0-11) at a given fret."""
    return (open_pitch + fret) % 12


def note_name_at_fret(open_pitch: int, fret: int, use_flats: bool = False) -> str:
    pc = note_at_fret(open_pitch, fret)
    return (CHROMATIC_FLATS if use_flats else CHROMATIC_SHARPS)[pc]


# ---------------------------------------------------------------------------
# CAGED System
# ---------------------------------------------------------------------------

CAGED_COLORS = {
    "C": "#ef5350",
    "A": "#ffa726",
    "G": "#66bb6a",
    "E": "#42a5f5",
    "D": "#ab47bc",
}

CAGED_TUNINGS = {"Standard (EADGBE)", "Half Step Down"}


def get_caged_zones(
    root_pc: int,
    tuning_pitches: list[int],
) -> list[tuple[str, float]]:
    """Return CAGED shape zones as (name, center_fret) sorted by center.

    Uses anchor frets on strings 0 (low E), 1 (A), and 2 (D) to compute
    a center fret for each shape.  Generates at base and +12 offsets to
    cover the full 15-fret range.
    """
    anchor_E = (root_pc - tuning_pitches[0] % 12) % 12
    anchor_A = (root_pc - tuning_pitches[1] % 12) % 12
    anchor_D = (root_pc - tuning_pitches[2] % 12) % 12

    shape_centers = {
        "C": anchor_A - 1,
        "A": anchor_A + 2,
        "G": anchor_E - 2,
        "E": anchor_E + 0.5,
        "D": anchor_D + 1,
    }

    zones: list[tuple[str, float]] = []
    for name, base in shape_centers.items():
        for offset in (0, 12):
            center = base + offset
            if -2 <= center <= 17:
                zones.append((name, center))

    zones.sort(key=lambda z: z[1])
    return zones


def assign_caged_shape(fret: int, zones: list[tuple[str, float]]) -> str:
    """Return the CAGED shape name whose center is nearest to *fret*."""
    best_name = zones[0][0]
    best_dist = abs(fret - zones[0][1])
    for name, center in zones[1:]:
        dist = abs(fret - center)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


# ---------------------------------------------------------------------------
# Slide Guitar — Chord Identification
# ---------------------------------------------------------------------------

CHORD_TEMPLATES: dict[str, set[int]] = {
    "":     {0, 4, 7},
    "m":    {0, 3, 7},
    "7":    {0, 4, 7, 10},
    "m7":   {0, 3, 7, 10},
    "maj7": {0, 4, 7, 11},
    "dim":  {0, 3, 6},
    "aug":  {0, 4, 8},
    "sus4": {0, 5, 7},
    "sus2": {0, 2, 7},
    "6":    {0, 4, 7, 9},
}


def identify_chord(pitches: list[int]) -> str:
    """Identify what chord 6 MIDI pitches form.

    Returns e.g. "C", "Am", "G7/B", or "?" if no match.
    """
    unique_pcs = {p % 12 for p in pitches}
    bass_pc = pitches[0] % 12

    best: tuple[int, str, int, int] | None = None  # (score, name, root, extra)

    for root_pc in unique_pcs:
        intervals = {(pc - root_pc) % 12 for pc in unique_pcs}
        for suffix, template in CHORD_TEMPLATES.items():
            if not template.issubset(intervals):
                continue
            extra = len(intervals) - len(template)
            score = 0
            if root_pc == bass_pc:
                score += 5
            # Prefer simpler templates (fewer notes = fewer extra)
            score -= extra
            # Prefer simpler quality (fewer template notes)
            score -= len(template)
            if best is None or score > best[0]:
                best = (score, suffix, root_pc, extra)

    if best is None:
        return "?"

    _, suffix, root_pc, _ = best
    root_name = CHROMATIC_SHARPS[root_pc]
    chord_name = root_name + suffix

    # Only show slash notation when bass is NOT a chord tone
    if root_pc != bass_pc:
        template = CHORD_TEMPLATES[suffix]
        bass_interval = (bass_pc - root_pc) % 12
        if bass_interval not in template:
            bass_name = CHROMATIC_SHARPS[bass_pc]
            chord_name += "/" + bass_name

    return chord_name
