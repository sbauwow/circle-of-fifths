import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from audio_player import ChordAudioPlayer
    from main import MainWindow

    HAS_QT = True
except ModuleNotFoundError:
    HAS_QT = False


@unittest.skipUnless(HAS_QT, "PySide6 is not installed")
class MainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_starts_in_a_complete_c_major_state(self):
        self.assertEqual(self.window.harmony.root.name, "C")
        self.assertEqual(self.window.harmony.mode, "Ionian")
        self.assertEqual(
            [chord.name for chord in self.window.harmony.chords],
            ["C", "Dm", "Em", "F", "G", "Am", "Bdim"],
        )

    def test_minor_ring_selection_updates_visible_mode(self):
        self.window.circle._select(0, True)

        self.assertEqual(self.window.mode_combo.currentText(), "Aeolian")
        self.assertEqual(self.window.harmony.root.name, "A")
        self.assertEqual(self.window.harmony.chords[0].name, "Am")

    def test_chord_selection_updates_both_visualizations(self):
        with patch.object(ChordAudioPlayer, "play", return_value=True):
            self.window.chord_strip._buttons[4].click()

        chord = self.window.harmony.chords[4]
        self.assertEqual(self.window.fretboard._active_chord, chord)
        self.assertEqual(self.window.circle._active_segment, (1, False))
        self.assertIn("G — G · B · D", self.window.status_label.text())

    def test_slide_mode_is_limited_to_compatible_tunings(self):
        self.assertFalse(self.window.slide_check.isEnabled())

        self.window.tuning_combo.setCurrentText("Open G (DGDGBD)")
        self.assertTrue(self.window.slide_check.isEnabled())

    def test_capo_mode_updates_fretboard_and_status(self):
        self.assertEqual(self.window.fretboard._capo_fret, 0)
        self.assertFalse(self.window.capo_spin.isEnabled())

        self.window.capo_check.setChecked(True)
        self.window.capo_spin.setValue(5)

        self.assertTrue(self.window.capo_spin.isEnabled())
        self.assertEqual(self.window.fretboard._capo_fret, 5)
        self.assertIn("Capo 5", self.window.status_label.text())

        self.window.capo_check.setChecked(False)
        self.assertEqual(self.window.fretboard._capo_fret, 0)
        self.assertNotIn("Capo", self.window.status_label.text())

    def test_moving_capo_preserves_selected_chord(self):
        with patch.object(ChordAudioPlayer, "play", return_value=True):
            self.window.chord_strip._buttons[4].click()
        chord = self.window.harmony.chords[4]

        self.window.capo_check.setChecked(True)
        self.window.capo_spin.setValue(3)

        self.assertEqual(self.window.active_chord, chord)
        self.assertEqual(self.window.fretboard._active_chord, chord)
        self.assertIn("G — G · B · D", self.window.status_label.text())
        self.assertIn("Capo 3", self.window.status_label.text())

    def test_capo_clamps_slide_selection_to_playable_frets(self):
        self.window.fretboard._slide_fret = 2
        self.window.fretboard.set_capo_fret(4)

        self.assertEqual(self.window.fretboard._slide_fret, 4)

        with self.assertRaises(ValueError):
            self.window.fretboard.set_capo_fret(13)


if __name__ == "__main__":
    unittest.main()
