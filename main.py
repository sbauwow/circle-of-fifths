#!/usr/bin/env python3
"""Circle of Fifths Visualizer — main entry point."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel,
    QMainWindow, QVBoxLayout, QWidget,
)

from theory import (
    KEY_SIGNATURES, MODE_NAMES, PROGRESSIONS, TUNING_NAMES, TUNINGS, Scale,
)
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
QLabel {
    color: #aaa;
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

        # Fretboard
        self.fretboard = FretboardWidget()
        layout.addWidget(self.fretboard, stretch=0)

        # Status bar
        self.status_label = QLabel("  Click a key on the circle to begin")
        self.statusBar().addPermanentWidget(self.status_label, 1)

        self._connect_signals()

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(40)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        # Mode
        layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MODE_NAMES)
        layout.addWidget(self.mode_combo)

        layout.addSpacing(15)

        # Progression
        layout.addWidget(QLabel("Progression:"))
        self.prog_combo = QComboBox()
        self.prog_combo.addItem("(none)")
        for prog in PROGRESSIONS:
            self.prog_combo.addItem(prog.name)
        layout.addWidget(self.prog_combo)

        layout.addSpacing(15)

        # Tuning
        layout.addWidget(QLabel("Tuning:"))
        self.tuning_combo = QComboBox()
        self.tuning_combo.addItems(TUNING_NAMES)
        layout.addWidget(self.tuning_combo)

        layout.addSpacing(15)

        # Show degrees
        self.degree_check = QCheckBox("Show Degrees")
        layout.addWidget(self.degree_check)

        layout.addStretch()
        return bar

    def _connect_signals(self):
        # Circle -> Fretboard
        self.circle.scale_changed.connect(self._on_scale_changed)
        # Circle -> Status
        self.circle.key_selected.connect(self._on_key_selected)
        # Mode -> Circle
        self.mode_combo.currentTextChanged.connect(self.circle.set_mode)
        # Progression -> Circle
        self.prog_combo.currentIndexChanged.connect(self._on_progression_changed)
        # Tuning -> Fretboard
        self.tuning_combo.currentTextChanged.connect(self._on_tuning_changed)
        # Degrees -> Fretboard
        self.degree_check.toggled.connect(self.fretboard.set_show_degrees)

    def _on_scale_changed(self, scale: Scale):
        self.fretboard.set_scale(scale)

    def _on_key_selected(self, name: str, is_minor: bool):
        quality = "Minor" if is_minor else "Major"
        mode = self.mode_combo.currentText()
        # Find position for sig
        from theory import CIRCLE_MAJOR_NAMES, CIRCLE_MINOR_NAMES
        names = CIRCLE_MINOR_NAMES if is_minor else CIRCLE_MAJOR_NAMES
        try:
            pos = names.index(name)
        except ValueError:
            pos = 0
        sharps, flats = KEY_SIGNATURES[pos]
        if sharps and not flats:
            sig = f"{sharps}\u266f"
        elif flats and not sharps:
            sig = f"{flats}\u266d"
        else:
            sig = "0\u266f 0\u266d"
        self.status_label.setText(f"  {name} {quality} \u2014 {mode} | {sig}")

    def _on_progression_changed(self, index: int):
        if index <= 0:
            self.circle.set_progression(None)
        else:
            self.circle.set_progression(PROGRESSIONS[index - 1])

    def _on_tuning_changed(self, name: str):
        tuning = TUNINGS.get(name)
        if tuning:
            self.fretboard.set_tuning(tuning)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("sans-serif", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
