"""Guitar fretboard custom widget — QPainter rendering."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from theory import (
    CAGED_COLORS, CHROMATIC_SHARPS, DEGREE_LABELS, Chord, GuitarTuning,
    Scale, TUNINGS,
    assign_caged_shape, get_caged_zones, identify_chord, note_at_fret,
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
COL_SLIDE_NOTE = "#e0e0e0"
COL_SLIDE_BAR = "#ffffff"
COL_FINGERSTYLE_SEP = "#5c6bc0"
COL_PIMA = "#ffcc80"
COL_CAPO = "#d7dde5"
COL_BLOCKED = "#10101d"

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
        self._active_chord: Chord | None = None
        self._show_degrees: bool = False
        self._caged_enabled: bool = False
        self._caged_shape: str | None = None  # None = "All"
        self._slide_mode: bool = False
        self._slide_fret: int | None = None
        self._fingerstyle: bool = False
        self._capo_fret: int = 0

    # -- Public API ----------------------------------------------------------

    def set_scale(self, scale: Scale | None):
        self._scale = scale
        self._active_chord = None
        self.update()

    def set_chord(self, chord: Chord | None):
        self._active_chord = chord
        self.update()

    def set_tuning(self, tuning: GuitarTuning):
        self._tuning = tuning
        self.update()

    def set_show_degrees(self, show: bool):
        self._show_degrees = show
        self.update()

    def set_caged(self, enabled: bool, shape: str | None = None):
        self._caged_enabled = enabled
        self._caged_shape = shape
        self.update()

    def set_slide_mode(self, enabled: bool):
        self._slide_mode = enabled
        if not enabled:
            self._slide_fret = None
        self.update()

    def set_fingerstyle(self, enabled: bool):
        self._fingerstyle = enabled
        self.update()

    def set_capo_fret(self, fret: int):
        if not 0 <= fret <= 12:
            raise ValueError("Capo fret must be between 0 and 12")
        self._capo_fret = fret
        if self._slide_fret is not None and self._slide_fret < fret:
            self._slide_fret = fret
        self.update()

    def _note_name(self, pitch_class: int) -> str:
        if self._scale is not None:
            for note in self._scale.notes:
                if note.pitch_class == pitch_class:
                    return note.name
        return CHROMATIC_SHARPS[pitch_class]

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
            pima_font = QFont("sans-serif", max(8, int(string_spacing * 0.30)))
            pima_letters = {0: "P", 1: "P", 2: "P", 3: "I", 4: "M", 5: "A"}
            for si in range(num_strings):
                y = fb_y + (num_strings - 1 - si) * string_spacing
                sounding_pc = (self._tuning.pitches[si] + self._capo_fret) % 12
                name = self._note_name(sounding_pc)
                fm = QFontMetricsF(label_font)
                if self._fingerstyle:
                    # Draw note name
                    p.setFont(label_font)
                    p.setPen(QColor(COL_LABEL))
                    name_w = fm.horizontalAdvance(name)
                    pfm = QFontMetricsF(pima_font)
                    finger = pima_letters.get(si, "")
                    finger_w = pfm.horizontalAdvance(" " + finger)
                    total_w = name_w + finger_w
                    text_x = label_w - 5 - total_w
                    p.drawText(QRectF(text_x, y - fm.height() / 2, name_w, fm.height()),
                                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                name)
                    # Draw PIMA letter in amber
                    p.setFont(pima_font)
                    p.setPen(QColor(COL_PIMA))
                    p.drawText(QRectF(text_x + name_w, y - pfm.height() / 2, finger_w, pfm.height()),
                                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                " " + finger)
                else:
                    p.setFont(label_font)
                    p.setPen(QColor(COL_LABEL))
                    p.drawText(QRectF(0, y - fm.height() / 2, label_w - 5, fm.height()),
                                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                                name)

            # Fret numbers / slide chord labels (below fretboard)
            if self._slide_mode:
                chord_font = QFont("sans-serif", max(6, int(min(string_spacing * 0.22, 9))))
                chord_font_bold = QFont("sans-serif", max(6, int(min(string_spacing * 0.22, 9))), QFont.Weight.Bold)
                fret_slot_w = fret_xs[1] - fret_xs[0] if len(fret_xs) > 1 else 40
                for f in range(self._capo_fret, NUM_FRETS + 1):
                    pitches_at_fret = [op + f for op in self._tuning.pitches]
                    chord_name = identify_chord(pitches_at_fret)
                    if f == 0:
                        mid_x = fret_xs[0] - 12
                    else:
                        mid_x = (fret_xs[f - 1] + fret_xs[f]) / 2
                    is_selected = (self._slide_fret == f)
                    p.setFont(chord_font_bold if is_selected else chord_font)
                    color = QColor("#ffffff") if is_selected else QColor(COL_FRET_NUM)
                    p.setPen(color)
                    nfm = QFontMetricsF(p.font())
                    rect_w = max(fret_slot_w * 0.9, 24)
                    p.drawText(QRectF(mid_x - rect_w / 2, fb_y + fb_h + 6, rect_w, nfm.height()),
                                Qt.AlignmentFlag.AlignCenter, chord_name)
            else:
                num_font = QFont("sans-serif", max(7, int(min(string_spacing * 0.25, 10))))
                p.setFont(num_font)
                p.setPen(QColor(COL_FRET_NUM))
                for f in range(1, NUM_FRETS + 1):
                    mid_x = (fret_xs[f - 1] + fret_xs[f]) / 2
                    nfm = QFontMetricsF(num_font)
                    color = QColor(COL_FRET_NUM)
                    if f < self._capo_fret:
                        color.setAlphaF(0.28)
                    p.setPen(color)
                    p.drawText(QRectF(mid_x - 10, fb_y + fb_h + 6, 20, nfm.height()),
                                Qt.AlignmentFlag.AlignCenter, str(f))

            if self._capo_fret:
                self._draw_capo(p, fb_y, fb_h, fret_xs)

            # Slide bar and note circles at selected fret
            if self._slide_mode and self._slide_fret is not None:
                sf = self._slide_fret
                if sf == 0:
                    bar_x = fret_xs[0] - (fret_xs[1] - fret_xs[0]) * 0.5
                    bar_w = (fret_xs[1] - fret_xs[0]) * 0.5
                else:
                    bar_x = fret_xs[sf - 1]
                    bar_w = fret_xs[sf] - fret_xs[sf - 1]
                # Translucent vertical bar
                bar_color = QColor(COL_SLIDE_BAR)
                bar_color.setAlphaF(0.2)
                p.setBrush(QBrush(bar_color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(QRectF(bar_x, fb_y - 5, bar_w, fb_h + 10))

                # Draw slide note circles
                scale_pcs = self._scale.pitch_classes if self._scale else set()
                root_pc = self._scale.root.pitch_class if self._scale else -1
                caged_zones = None
                if self._caged_enabled and self._scale:
                    caged_zones = get_caged_zones(root_pc, self._tuning.pitches)
                note_r = min(string_spacing * 0.35, (fret_xs[1] - fret_xs[0]) * 0.3, 14)
                note_font = QFont("sans-serif", max(7, int(note_r * 0.85)), QFont.Weight.Bold)
                p.setFont(note_font)
                for si in range(num_strings):
                    open_pitch = self._tuning.pitches[si]
                    pc = (open_pitch + sf) % 12
                    y = fb_y + (num_strings - 1 - si) * string_spacing
                    if sf == 0:
                        x = fret_xs[0] - note_r - 4
                    else:
                        x = (fret_xs[sf - 1] + fret_xs[sf]) / 2
                    # Determine color: scale notes get normal color, others get neutral
                    in_scale = pc in scale_pcs
                    if in_scale and caged_zones:
                        shape = assign_caged_shape(sf, caged_zones)
                        color = QColor(CAGED_COLORS[shape])
                        if self._caged_shape is not None and shape != self._caged_shape:
                            color.setAlphaF(0.3)
                    elif in_scale:
                        color = QColor(COL_ROOT if pc == root_pc else COL_SCALE)
                    else:
                        color = QColor(COL_SLIDE_NOTE)
                    p.setBrush(QBrush(color))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(x - note_r, y - note_r, note_r * 2, note_r * 2)
                    # Label
                    p.setPen(QColor(COL_NOTE_TEXT if in_scale else "#333333"))
                    p.drawText(QRectF(x - note_r, y - note_r, note_r * 2, note_r * 2),
                                Qt.AlignmentFlag.AlignCenter, self._note_name(pc))

            # Fingerstyle bass/treble separator
            if self._fingerstyle and num_strings >= 4:
                sep_y = fb_y + (num_strings - 1 - 2.5) * string_spacing
                sep_color = QColor(COL_FINGERSTYLE_SEP)
                sep_color.setAlphaF(0.4)
                pen = QPen(sep_color, 2, Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.drawLine(int(fb_x), int(sep_y), int(fb_x + fb_w), int(sep_y))

            # Note markers
            if self._scale:
                self._draw_notes(p, fb_x, fb_y, fb_w, fb_h, fret_xs,
                                  string_spacing, num_strings)

    def _draw_notes(self, p: QPainter, fb_x, fb_y, fb_w, fb_h,
                     fret_xs, string_spacing, num_strings):
        scale = self._scale
        chord = self._active_chord
        highlighted = chord.pitch_classes if chord is not None else scale.pitch_classes
        root_pc = chord.root.pitch_class if chord is not None else scale.root.pitch_class

        note_r = min(string_spacing * 0.35, (fret_xs[1] - fret_xs[0]) * 0.3, 14)
        note_font = QFont("sans-serif", max(7, int(note_r * 0.85)), QFont.Weight.Bold)
        p.setFont(note_font)

        # Compute CAGED zones if enabled
        caged_zones = None
        if self._caged_enabled:
            caged_zones = get_caged_zones(scale.root.pitch_class, self._tuning.pitches)
            # Draw shape labels above fretboard
            self._draw_caged_labels(p, fb_y, fret_xs, caged_zones)

        for si in range(num_strings):
            open_pitch = self._tuning.pitches[si]
            y = fb_y + (num_strings - 1 - si) * string_spacing

            for fret in range(self._capo_fret, NUM_FRETS + 1):
                pc = note_at_fret(open_pitch, fret)
                if pc not in highlighted:
                    continue

                is_root = (pc == root_pc)

                # X position: center of fret space (or left of nut for open)
                if fret == 0:
                    x = fret_xs[0] - note_r - 4
                else:
                    x = (fret_xs[fret - 1] + fret_xs[fret]) / 2

                # Determine color
                if caged_zones:
                    shape = assign_caged_shape(fret, caged_zones)
                    color = QColor(CAGED_COLORS[shape])
                    # Dim notes not in the selected shape
                    if self._caged_shape is not None and shape != self._caged_shape:
                        color.setAlphaF(0.3)
                else:
                    color = QColor(COL_ROOT if is_root else COL_SCALE)

                # Draw circle
                p.setBrush(QBrush(color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(x - note_r, y - note_r, note_r * 2, note_r * 2)

                # Root outline when CAGED is active
                if caged_zones and is_root:
                    outline = QColor("#ffffff")
                    if self._caged_shape is not None and shape != self._caged_shape:
                        outline.setAlphaF(0.3)
                    p.setPen(QPen(outline, 2))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawEllipse(x - note_r, y - note_r, note_r * 2, note_r * 2)

                # Label
                if self._show_degrees:
                    interval = (pc - root_pc) % 12
                    text = DEGREE_LABELS.get(interval, "?")
                else:
                    text = self._note_name(pc)

                text_color = QColor(COL_NOTE_TEXT)
                if caged_zones and self._caged_shape is not None and shape != self._caged_shape:
                    text_color.setAlphaF(0.3)
                p.setPen(text_color)
                p.drawText(QRectF(x - note_r, y - note_r, note_r * 2, note_r * 2),
                            Qt.AlignmentFlag.AlignCenter, text)

    def _draw_capo(self, p: QPainter, fb_y: float, fb_h: float,
                   fret_xs: list[float]):
        """Shade inaccessible frets and draw the capo at its physical fret."""
        fret = self._capo_fret
        capo_x = (fret_xs[fret - 1] + fret_xs[fret]) / 2

        blocked = QColor(COL_BLOCKED)
        blocked.setAlphaF(0.72)
        p.fillRect(
            QRectF(fret_xs[0], fb_y - 5, capo_x - fret_xs[0] - 4, fb_h + 10),
            blocked,
        )

        p.setBrush(QBrush(QColor(COL_CAPO)))
        p.setPen(QPen(QColor("#7b8490"), 1))
        p.drawRoundedRect(QRectF(capo_x - 4, fb_y - 12, 8, fb_h + 24), 4, 4)
        p.drawEllipse(QRectF(capo_x - 6, fb_y - 17, 12, 12))
        p.drawEllipse(QRectF(capo_x - 6, fb_y + fb_h + 5, 12, 12))

    def _draw_caged_labels(self, p: QPainter, fb_y: float,
                            fret_xs: list[float],
                            zones: list[tuple[str, float]]):
        """Draw CAGED shape name labels above the top string."""
        label_font = QFont("sans-serif", 9, QFont.Weight.Bold)
        p.setFont(label_font)
        for name, center in zones:
            # Map center fret to pixel x
            if center <= 0:
                x = fret_xs[0]
            elif center >= NUM_FRETS:
                x = fret_xs[NUM_FRETS]
            else:
                lo = int(center)
                frac = center - lo
                x = fret_xs[lo] + frac * (fret_xs[lo + 1] - fret_xs[lo])
            color = QColor(CAGED_COLORS[name])
            if self._caged_shape is not None and name != self._caged_shape:
                color.setAlphaF(0.3)
            if center < self._capo_fret:
                color.setAlphaF(0.15)
            p.setPen(color)
            p.drawText(QRectF(x - 12, fb_y - 20, 24, 16),
                        Qt.AlignmentFlag.AlignCenter, name)

    # -- Mouse interaction ---------------------------------------------------

    def mousePressEvent(self, event):
        if not self._slide_mode:
            return super().mousePressEvent(event)
        x = event.position().x()
        label_w = 40
        right_pad = 15
        fb_x = label_w
        fb_w = self.width() - label_w - right_pad
        if fb_w <= 0:
            return
        rel = (x - fb_x) / fb_w * NUM_FRETS
        fret = max(self._capo_fret, min(NUM_FRETS, round(rel)))
        self._slide_fret = fret
        self.update()
