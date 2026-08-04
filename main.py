#!/usr/bin/env python3
"""Circle of Fifths Visualizer — main entry point."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel,
    QMainWindow, QSpinBox, QVBoxLayout, QWidget,
)

from theory import (
    CAGED_TUNINGS, MODE_NAMES, PROGRESSIONS, SLIDE_TUNINGS, TUNING_NAMES,
    TUNINGS, Chord, HarmonyState,
)
from audio_player import ChordAudioPlayer
from chord_strip import DiatonicChordStrip
from circle_widget import CircleOfFifthsWidget
from fretboard_widget import FretboardWidget

STYLESHEET = """
QMainWindow {
    background: #1a1a2e;
}
QWidget {
    color: #e0e0e0;
    font-family: sans-serif;
}
QComboBox {
    background: #2a2a3e;
    border: 1px solid #555;
    padding: 4px 8px;
    color: #e0e0e0;
    border-radius: 3px;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #e0e0e0;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #2a2a3e;
    color: #e0e0e0;
    selection-background-color: #0f3460;
    border: 1px solid #555;
}
QSpinBox {
    background: #2a2a3e;
    border: 1px solid #555;
    border-radius: 3px;
    color: #e0e0e0;
    padding: 3px 5px;
    min-width: 66px;
}
QSpinBox:disabled {
    color: #68737a;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555;
    border-radius: 3px;
    background: #2a2a3e;
}
QCheckBox::indicator:checked {
    background: #4fc3f7;
    border-color: #4fc3f7;
}
QCheckBox:disabled {
    color: #68737a;
}
QLabel {
    color: #aaa;
}
QLabel#chord-strip-title {
    color: #90a4ae;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#diatonic-chord {
    background: #20263a;
    border: 1px solid #344052;
    border-radius: 4px;
    padding: 5px 8px;
    color: #cfd8dc;
    font-size: 11px;
}
QPushButton#diatonic-chord:hover {
    border-color: #607d8b;
    background: #273149;
}
QPushButton#diatonic-chord:checked {
    border-color: #f06292;
    background: #5a2942;
    color: #ffffff;
}
QPushButton#diatonic-chord:focus {
    border: 2px solid #4fc3f7;
}
QStatusBar {
    background: #16213e;
    color: #90a4ae;
    border-top: 1px solid #22334a;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Circle of Fifths")
        self.setMinimumSize(900, 750)
        self.resize(1000, 800)
        self.setStyleSheet(STYLESHEET)
        self.harmony: HarmonyState | None = None
        self.active_chord: Chord | None = None
        self.capo_fret = 0
        self.audio = ChordAudioPlayer(self)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 0)

        # Toolbar
        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        # Circle of Fifths
        self.circle = CircleOfFifthsWidget()
        layout.addWidget(self.circle, stretch=3)

        self.chord_strip = DiatonicChordStrip()
        layout.addWidget(self.chord_strip)

        # Fretboard
        self.fretboard = FretboardWidget()
        layout.addWidget(self.fretboard, stretch=0)

        # Status bar
        self.status_label = QLabel("  Click a key on the circle to begin")
        self.statusBar().addPermanentWidget(self.status_label, 1)

        self._connect_signals()
        self._on_tuning_changed(self.tuning_combo.currentText())
        self.circle.select_key("C", "Ionian")

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(72)
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        primary = QHBoxLayout()
        primary.setContentsMargins(0, 0, 0, 0)
        primary.setSpacing(8)
        outer.addLayout(primary)

        # Mode
        primary.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MODE_NAMES)
        primary.addWidget(self.mode_combo)

        # Progression
        primary.addWidget(QLabel("Progression:"))
        self.prog_combo = QComboBox()
        self.prog_combo.addItem("(none)")
        for prog in PROGRESSIONS:
            self.prog_combo.addItem(prog.name)
        self.prog_combo.setMinimumWidth(150)
        primary.addWidget(self.prog_combo)

        # Tuning
        primary.addWidget(QLabel("Tuning:"))
        self.tuning_combo = QComboBox()
        self.tuning_combo.addItems(TUNING_NAMES)
        self.tuning_combo.setMinimumWidth(175)
        primary.addWidget(self.tuning_combo)
        primary.addStretch()

        display = QHBoxLayout()
        display.setContentsMargins(0, 0, 0, 0)
        display.setSpacing(12)
        outer.addLayout(display)
        display.addWidget(QLabel("Fretboard:"))

        # Show degrees
        self.degree_check = QCheckBox("Degrees")
        display.addWidget(self.degree_check)

        # CAGED overlay
        self.caged_check = QCheckBox("CAGED")
        display.addWidget(self.caged_check)
        self.caged_combo = QComboBox()
        self.caged_combo.addItems(["All", "C", "A", "G", "E", "D"])
        self.caged_combo.setVisible(False)
        display.addWidget(self.caged_combo)

        # Slide mode
        self.slide_check = QCheckBox("Slide")
        display.addWidget(self.slide_check)

        # Fingerstyle mode
        self.fingerstyle_check = QCheckBox("Fingerstyle")
        display.addWidget(self.fingerstyle_check)

        # Capo mode
        self.capo_check = QCheckBox("Capo")
        display.addWidget(self.capo_check)
        self.capo_spin = QSpinBox()
        self.capo_spin.setRange(1, 12)
        self.capo_spin.setPrefix("Fret ")
        self.capo_spin.setEnabled(False)
        self.capo_spin.setToolTip("Physical fret where the capo is placed")
        display.addWidget(self.capo_spin)

        display.addStretch()
        return bar

    def _connect_signals(self):
        # Circle -> shared harmony consumers
        self.circle.harmony_changed.connect(self._on_harmony_changed)
        self.circle.mode_resolved.connect(self._on_mode_resolved)
        # Mode -> Circle
        self.mode_combo.currentTextChanged.connect(self.circle.set_mode)
        # Progression -> Circle
        self.prog_combo.currentIndexChanged.connect(self._on_progression_changed)
        # Tuning -> Fretboard
        self.tuning_combo.currentTextChanged.connect(self._on_tuning_changed)
        # Degrees -> Fretboard
        self.degree_check.toggled.connect(self.fretboard.set_show_degrees)
        # CAGED -> Fretboard
        self.caged_check.toggled.connect(self._on_caged_toggled)
        self.caged_combo.currentTextChanged.connect(self._on_caged_shape_changed)
        # Slide -> Fretboard
        self.slide_check.toggled.connect(self.fretboard.set_slide_mode)
        # Fingerstyle -> Fretboard
        self.fingerstyle_check.toggled.connect(self.fretboard.set_fingerstyle)
        # Capo -> Fretboard
        self.capo_check.toggled.connect(self._on_capo_toggled)
        self.capo_spin.valueChanged.connect(self._on_capo_value_changed)
        # Chord strip -> circle, fretboard, and audio
        self.chord_strip.chord_selected.connect(self._on_chord_selected)

    def _on_harmony_changed(self, harmony: HarmonyState):
        self.harmony = harmony
        self.active_chord = None
        self.fretboard.set_scale(harmony.scale)
        self.chord_strip.set_harmony(harmony)
        self._show_harmony_status()

    def _show_harmony_status(self):
        if self.harmony is None:
            return
        harmony = self.harmony
        scale_notes = " · ".join(note.name for note in harmony.scale.notes)
        self.status_label.setText(
            f"  {harmony.root.name} {harmony.mode} — {harmony.signature_label}"
            f"  |  {scale_notes}{self._capo_status()}")

    def _on_mode_resolved(self, mode: str):
        blocked = self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText(mode)
        self.mode_combo.blockSignals(blocked)

    def _on_chord_selected(self, chord: Chord | None):
        self.active_chord = chord
        self.circle.set_active_chord(chord)
        self.fretboard.set_chord(chord)
        if chord is None:
            if self.harmony is not None:
                self._on_harmony_changed(self.harmony)
            return

        audio_status = "" if self.audio.play(chord) else "  |  audio unavailable"
        self._show_chord_status(chord, audio_status)

    def _show_chord_status(self, chord: Chord, audio_status: str = ""):
        notes = " · ".join(note.name for note in chord.notes)
        self.status_label.setText(
            f"  {chord.roman}  {chord.name} — {notes}{self._capo_status()}"
            f"{audio_status}")

    def _on_progression_changed(self, index: int):
        if index <= 0:
            self.circle.set_progression(None)
        else:
            self.circle.set_progression(PROGRESSIONS[index - 1])

    def _on_tuning_changed(self, name: str):
        tuning = TUNINGS.get(name)
        if tuning:
            self.fretboard.set_tuning(tuning)
        # CAGED only valid for standard-interval tunings
        supported = name in CAGED_TUNINGS
        self.caged_check.setEnabled(supported)
        if not supported:
            self.caged_check.setChecked(False)

        slide_supported = name in SLIDE_TUNINGS
        self.slide_check.setEnabled(slide_supported)
        self.slide_check.setToolTip(
            "Straight-bar chord positions for open tunings"
            if slide_supported else "Choose an open or modal tuning for slide positions")
        if not slide_supported:
            self.slide_check.setChecked(False)

    def _on_caged_toggled(self, checked: bool):
        self.caged_combo.setVisible(checked)
        if not checked:
            self.caged_combo.setCurrentIndex(0)
        shape = None if not checked or self.caged_combo.currentText() == "All" else self.caged_combo.currentText()
        self.fretboard.set_caged(checked, shape)

    def _on_caged_shape_changed(self, text: str):
        if not self.caged_check.isChecked():
            return
        shape = None if text == "All" else text
        self.fretboard.set_caged(True, shape)

    def _on_capo_toggled(self, checked: bool):
        self.capo_spin.setEnabled(checked)
        self._set_capo_fret(self.capo_spin.value() if checked else 0)

    def _on_capo_value_changed(self, fret: int):
        if self.capo_check.isChecked():
            self._set_capo_fret(fret)

    def _set_capo_fret(self, fret: int):
        self.capo_fret = fret
        self.fretboard.set_capo_fret(fret)
        if self.active_chord is not None:
            self._show_chord_status(self.active_chord)
        else:
            self._show_harmony_status()

    def _capo_status(self) -> str:
        return f"  |  Capo {self.capo_fret}" if self.capo_fret else ""


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("sans-serif", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
