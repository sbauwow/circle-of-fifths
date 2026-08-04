from array import array
import unittest

from synth import chord_midi_notes, midi_frequency, synthesize_chord


class SynthTests(unittest.TestCase):
    def test_standard_pitch(self):
        self.assertAlmostEqual(midi_frequency(69), 440.0)

    def test_chord_is_voiced_upward_from_root(self):
        self.assertEqual(chord_midi_notes(0, {0, 4, 7}), [48, 52, 55])
        self.assertEqual(chord_midi_notes(9, {0, 4, 9}), [57, 60, 64])

    def test_pcm_has_expected_length_and_signal(self):
        pcm = synthesize_chord(
            0, {0, 4, 7}, sample_rate=8_000, duration=0.1)
        samples = array("h")
        samples.frombytes(pcm)

        self.assertEqual(len(pcm), 8_000 // 10 * 2)
        self.assertTrue(any(sample != 0 for sample in samples))
        self.assertLessEqual(max(abs(sample) for sample in samples), 32767)

    def test_invalid_audio_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            synthesize_chord(0, {0, 4, 7}, sample_rate=0)
        with self.assertRaises(ValueError):
            synthesize_chord(0, {0, 4, 7}, duration=0)


if __name__ == "__main__":
    unittest.main()
