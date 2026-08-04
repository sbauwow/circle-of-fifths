"""Clickable diatonic chord strip shared by exploration and practice flows."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from theory import Chord, HarmonyState


class DiatonicChordStrip(QWidget):
    chord_selected = Signal(object)  # Chord | None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("diatonic-strip")
        self._harmony: HarmonyState | None = None
        self._buttons: list[QPushButton] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(5)

        self._title = QLabel("Diatonic chords")
        self._title.setObjectName("chord-strip-title")
        outer.addWidget(self._title)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        outer.addLayout(row)

        for index in range(7):
            button = QPushButton("—")
            button.setObjectName("diatonic-chord")
            button.setCheckable(True)
            button.setEnabled(False)
            button.setMinimumHeight(48)
            button.clicked.connect(
                lambda checked, chord_index=index: self._select(chord_index, checked))
            self._buttons.append(button)
            row.addWidget(button, 1)

    def set_harmony(self, harmony: HarmonyState):
        self._harmony = harmony
        self._title.setText(
            f"Diatonic chords  ·  {harmony.root.name} {harmony.mode}")
        for button, chord in zip(self._buttons, harmony.chords):
            notes = " · ".join(note.name for note in chord.notes)
            button.setText(f"{chord.roman}\n{chord.name}")
            button.setToolTip(f"{chord.name}: {notes}")
            button.setAccessibleName(
                f"{chord.roman}, {chord.name}, notes {' '.join(note.name for note in chord.notes)}")
            button.setEnabled(True)
            button.setChecked(False)

    def clear_selection(self):
        for button in self._buttons:
            button.setChecked(False)

    def _select(self, index: int, checked: bool):
        if self._harmony is None:
            return
        for other_index, button in enumerate(self._buttons):
            if other_index != index:
                button.setChecked(False)
        chord: Chord | None = self._harmony.chords[index] if checked else None
        self.chord_selected.emit(chord)
