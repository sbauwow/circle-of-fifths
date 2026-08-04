import unittest

from theory import (
    HarmonyState,
    PROGRESSIONS,
    TUNINGS,
    circle_segment_for_chord,
    identify_chord,
)


class HarmonyStateTests(unittest.TestCase):
    def test_c_ionian_diatonic_chords(self):
        harmony = HarmonyState.build("C", "Ionian")

        self.assertEqual(
            [chord.roman for chord in harmony.chords],
            ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
        )
        self.assertEqual(
            [chord.name for chord in harmony.chords],
            ["C", "Dm", "Em", "F", "G", "Am", "Bdim"],
        )
        self.assertEqual(harmony.signature_label, "no sharps or flats")

    def test_a_aeolian_uses_minor_harmony(self):
        harmony = HarmonyState.build("A", "Aeolian")

        self.assertEqual(
            [chord.roman for chord in harmony.chords],
            ["i", "ii°", "III", "iv", "v", "VI", "VII"],
        )
        self.assertEqual(
            [chord.name for chord in harmony.chords],
            ["Am", "Bdim", "C", "Dm", "Em", "F", "G"],
        )

    def test_modal_spelling_drives_signature_and_chords(self):
        harmony = HarmonyState.build("D", "Dorian")

        self.assertEqual(
            [note.name for note in harmony.scale.notes],
            ["D", "E", "F", "G", "A", "B", "C"],
        )
        self.assertEqual(harmony.signature_label, "no sharps or flats")
        self.assertEqual(harmony.chords[0].name, "Dm")

    def test_flat_key_spelling_is_retained_in_chords(self):
        harmony = HarmonyState.build("Db", "Ionian")

        self.assertEqual(
            [note.name for note in harmony.scale.notes],
            ["Db", "Eb", "F", "Gb", "Ab", "Bb", "C"],
        )
        self.assertEqual(
            [chord.name for chord in harmony.chords[:3]],
            ["Db", "Ebm", "Fm"],
        )
        self.assertEqual(harmony.signature_label, "5 flats")

    def test_progression_uses_active_mode(self):
        harmony = HarmonyState.build("A", "Aeolian")

        self.assertEqual(
            [chord.name for chord in PROGRESSIONS[0].in_harmony(harmony)],
            ["Am", "Dm", "Em", "Am"],
        )

    def test_circle_segments_respect_chord_quality(self):
        harmony = HarmonyState.build("C", "Ionian")

        self.assertEqual(circle_segment_for_chord(harmony.chords[0]), (0, False))
        self.assertEqual(circle_segment_for_chord(harmony.chords[5]), (0, True))
        self.assertIsNone(circle_segment_for_chord(harmony.chords[6]))


class ChordIdentificationTests(unittest.TestCase):
    def test_open_g_reports_its_inversion(self):
        pitches = TUNINGS["Open G (DGDGBD)"].pitches
        self.assertEqual(identify_chord(pitches), "G/D")

    def test_unrelated_extra_notes_are_not_hidden(self):
        pitches = TUNINGS["Standard (EADGBE)"].pitches
        self.assertEqual(identify_chord(pitches), "?")


if __name__ == "__main__":
    unittest.main()
