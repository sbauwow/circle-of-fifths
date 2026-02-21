"""Guitar fretboard custom widget — QPainter rendering."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from theory import (
    CHROMATIC_FLATS, CHROMATIC_SHARPS, DEGREE_LABELS, GuitarTuning, Scale,
    TUNINGS, note_at_fret,
)

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

COL_BG = "#1a1a2e"
COL_WOOD = "#3e2723"
COL_NUT = "#fafafa"
COL_FRET = "#bdbdbd"
COL_STRING = "#9e9e9e"
COL_MARKER = "#4e342e"
COL_ROOT = "#ff7043"
COL_SCALE = "#26a69a"
COL_NOTE_TEXT = "#ffffff"
COL_FRET_NUM = "#90a4ae"
COL_LABEL = "#e0e0e0"

NUM_FRETS = 15
SINGLE_MARKERS = {3, 5, 7, 9, 15}
DOUBLE_MARKERS = {12}


class FretboardWidget(QWidget):
    """Horizontal guitar fretboard visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(180)
        self.setFixedHeight(200)
        self.setMinimumWidth(500)

        self._tuning: GuitarTuning = TUNINGS["Standard (EADGBE)"]
        self._scale: Scale | None = None
        self._show_degrees: bool = False

    # -- Public API ----------------------------------------------------------

    def set_scale(self, scale: Scale | None):
        self._scale = scale
        self.update()

    def set_tuning(self, tuning: GuitarTuning):
        self._tuning = tuning
        self.update()

    def set_show_degrees(self, show: bool):
        self._show_degrees = show
        self.update()

    # -- Paint ---------------------------------------------------------------

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        num_strings = len(self._tuning.pitches)

        # Layout
        label_w = 40       # space for string labels
        right_pad = 15
        top_pad = 25
        bottom_pad = 25
        fb_x = label_w
        fb_w = w - label_w - right_pad
        fb_y = top_pad
        fb_h = h - top_pad - bottom_pad
        string_spacing = fb_h / (num_strings - 1) if num_strings > 1 else fb_h

        # Fret x-positions (equal spacing for clarity)
        fret_xs = []
        for f in range(NUM_FRETS + 1):
            fret_xs.append(fb_x + fb_w * f / NUM_FRETS)

        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Background
            p.fillRect(self.rect(), QColor(COL_BG))

            # Fretboard body
            p.setBrush(QBrush(QColor(COL_WOOD)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(fb_x, fb_y - 5, fb_w, fb_h + 10), 4, 4)

            # Fret markers (dots)
            for fret in range(1, NUM_FRETS + 1):
                if fret in SINGLE_MARKERS or fret in DOUBLE_MARKERS:
                    mid_x = (fret_xs[fret - 1] + fret_xs[fret]) / 2
                    dot_r = min(string_spacing * 0.2, 6)
                    p.setBrush(QBrush(QColor(COL_MARKER)))
                    p.setPen(Qt.PenStyle.NoPen)
                    if fret in DOUBLE_MARKERS:
                        y1 = fb_y + string_spacing * 1.5
                        y2 = fb_y + string_spacing * 3.5
                        p.drawEllipse(mid_x - dot_r, y1 - dot_r, dot_r * 2, dot_r * 2)
                        p.drawEllipse(mid_x - dot_r, y2 - dot_r, dot_r * 2, dot_r * 2)
                    else:
                        mid_y = fb_y + fb_h / 2
                        p.drawEllipse(mid_x - dot_r, mid_y - dot_r, dot_r * 2, dot_r * 2)

            # Nut (fret 0)
            p.setPen(QPen(QColor(COL_NUT), 4))
            p.drawLine(int(fret_xs[0]), int(fb_y - 5), int(fret_xs[0]), int(fb_y + fb_h + 5))

            # Fret wires
            fret_pen = QPen(QColor(COL_FRET), 1.5)
            for f in range(1, NUM_FRETS + 1):
                p.setPen(fret_pen)
                x = fret_xs[f]
                p.drawLine(int(x), int(fb_y - 3), int(x), int(fb_y + fb_h + 3))

            # Strings (bottom = low, top = high — standard guitar orientation reversed
            # so index 0 (low E) is at bottom)
            for si in range(num_strings):
                y = fb_y + (num_strings - 1 - si) * string_spacing
                thickness = 1.0 + si * 0.4  # low strings thicker
                p.setPen(QPen(QColor(COL_STRING), thickness))
                p.drawLine(int(fb_x), int(y), int(fb_x + fb_w), int(y))

            # String labels (to the left of nut)
            label_font = QFont("sans-serif", max(9, int(string_spacing * 0.35)), QFont.Weight.Bold)
            p.setFont(label_font)
            p.setPen(QColor(COL_LABEL))
            for si in range(num_strings):
                y = fb_y + (num_strings - 1 - si) * string_spacing
                name = CHROMATIC_SHARPS[self._tuning.pitches[si] % 12]
                fm = QFontMetricsF(label_font)
                p.drawText(QRectF(0, y - fm.height() / 2, label_w - 5, fm.height()),
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                            name)

            # Fret numbers (below fretboard)
            num_font = QFont("sans-serif", max(7, int(min(string_spacing * 0.25, 10))))
            p.setFont(num_font)
            p.setPen(QColor(COL_FRET_NUM))
            for f in range(1, NUM_FRETS + 1):
                mid_x = (fret_xs[f - 1] + fret_xs[f]) / 2
                nfm = QFontMetricsF(num_font)
                p.drawText(QRectF(mid_x - 10, fb_y + fb_h + 6, 20, nfm.height()),
                            Qt.AlignmentFlag.AlignCenter, str(f))

            # Note markers
            if self._scale:
                self._draw_notes(p, fb_x, fb_y, fb_w, fb_h, fret_xs,
                                  string_spacing, num_strings)

    def _draw_notes(self, p: QPainter, fb_x, fb_y, fb_w, fb_h,
                     fret_xs, string_spacing, num_strings):
        scale = self._scale
        highlighted = scale.pitch_classes
        root_pc = scale.root.pitch_class

        note_r = min(string_spacing * 0.35, (fret_xs[1] - fret_xs[0]) * 0.3, 14)
        note_font = QFont("sans-serif", max(7, int(note_r * 0.85)), QFont.Weight.Bold)
        p.setFont(note_font)

        for si in range(num_strings):
            open_pitch = self._tuning.pitches[si]
            y = fb_y + (num_strings - 1 - si) * string_spacing

            for fret in range(0, NUM_FRETS + 1):
                pc = note_at_fret(open_pitch, fret)
                if pc not in highlighted:
                    continue

                is_root = (pc == root_pc)

                # X position: center of fret space (or left of nut for open)
                if fret == 0:
                    x = fret_xs[0] - note_r - 4
                else:
                    x = (fret_xs[fret - 1] + fret_xs[fret]) / 2

                # Draw circle
                color = COL_ROOT if is_root else COL_SCALE
                p.setBrush(QBrush(QColor(color)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(x - note_r, y - note_r, note_r * 2, note_r * 2)

                # Label
                if self._show_degrees:
                    interval = (pc - root_pc) % 12
                    text = DEGREE_LABELS.get(interval, "?")
                else:
                    text = CHROMATIC_SHARPS[pc]

                p.setPen(QColor(COL_NOTE_TEXT))
                p.drawText(QRectF(x - note_r, y - note_r, note_r * 2, note_r * 2),
                            Qt.AlignmentFlag.AlignCenter, text)
