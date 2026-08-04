"""Circle of Fifths custom widget — QPainter rendering + mouse interaction."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from theory import (
    CIRCLE_MAJOR_NAMES, CIRCLE_MINOR_NAMES, ENHARMONIC_MAJOR,
    ENHARMONIC_MINOR, KEY_SIGNATURES, Chord, HarmonyState, Progression,
    circle_position_for_pitch, circle_segment_for_chord,
)

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

COL_BG = "#1a1a2e"
COL_MAJOR_SEG = "#0f3460"
COL_MINOR_SEG = "#0a2647"
COL_SELECTED = "#4fc3f7"
COL_SELECTED_DIM = "#1a6e96"
COL_RELATIVE = "#29b6f6"
COL_MODE_HIGHLIGHT = "#ffb74d"
COL_PROGRESSION = "#f06292"
COL_ACTIVE_CHORD = "#ec6fa4"
COL_BORDER = "#22334a"
COL_TEXT = "#e0e0e0"
COL_TEXT_DIM = "#90a4ae"
COL_CENTER_BG = "#16213e"


class CircleOfFifthsWidget(QWidget):
    """Interactive circle-of-fifths visualization."""

    key_selected = Signal(str, bool)   # (key_name, is_minor)
    scale_changed = Signal(object)     # Scale; retained for API compatibility
    harmony_changed = Signal(object)   # HarmonyState
    mode_resolved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(300, 300)

        self._selected_pos: int | None = None
        self._selected_minor: bool = False
        self._mode: str = "Ionian"
        self._progression: Progression | None = None
        self._harmony: HarmonyState | None = None
        self._diatonic_segments: set[tuple[int, bool]] = set()
        self._active_segment: tuple[int, bool] | None = None

    # -- Public API ----------------------------------------------------------

    def set_mode(self, mode: str):
        if mode == self._mode:
            return
        root_name = self._selected_root_name()
        self._mode = mode
        if root_name is not None:
            state = HarmonyState.build(root_name, mode)
            segment = circle_segment_for_chord(state.chords[0])
            if segment is None:
                segment = (circle_position_for_pitch(state.root.pitch_class), False)
            self._selected_pos, self._selected_minor = segment
        self._recompute()
        self.update()

    def set_progression(self, prog: Progression | None):
        self._progression = prog
        self.update()

    def set_active_chord(self, chord: Chord | None):
        self._active_segment = (
            circle_segment_for_chord(chord) if chord is not None else None)
        self.update()

    def select_key(self, root_name: str, mode: str = "Ionian"):
        state = HarmonyState.build(root_name, mode)
        segment = circle_segment_for_chord(state.chords[0])
        if segment is None:
            segment = (circle_position_for_pitch(state.root.pitch_class), False)
        self._selected_pos, self._selected_minor = segment
        self._mode = mode
        self.mode_resolved.emit(mode)
        self._recompute()
        self.update()

    # -- Selection -----------------------------------------------------------

    def _select(self, pos: int, minor: bool):
        self._selected_pos = pos
        self._selected_minor = minor
        resolved_mode = "Aeolian" if minor else "Ionian"
        if self._mode != resolved_mode:
            self._mode = resolved_mode
            self.mode_resolved.emit(resolved_mode)
        name = CIRCLE_MINOR_NAMES[pos] if minor else CIRCLE_MAJOR_NAMES[pos]
        self.key_selected.emit(name, minor)
        self._recompute()
        self.update()

    def _selected_root_name(self) -> str | None:
        if self._selected_pos is None:
            return None
        if self._selected_minor:
            return CIRCLE_MINOR_NAMES[self._selected_pos][:-1]
        return CIRCLE_MAJOR_NAMES[self._selected_pos]

    def _recompute(self):
        """Build the shared harmony and derive exact major/minor segments."""
        if self._selected_pos is None:
            self._harmony = None
            self._diatonic_segments = set()
            self._active_segment = None
            return

        self._harmony = HarmonyState.build(self._selected_root_name(), self._mode)
        segments = (
            circle_segment_for_chord(chord) for chord in self._harmony.chords)
        self._diatonic_segments = {segment for segment in segments if segment is not None}
        self._active_segment = None
        self.harmony_changed.emit(self._harmony)
        self.scale_changed.emit(self._harmony.scale)

    # -- Geometry helpers ----------------------------------------------------

    def _geometry(self):
        cx = self.width() / 2
        cy = self.height() / 2
        r = min(cx, cy) * 0.90
        return cx, cy, r

    @staticmethod
    def _segment_angles(i: int):
        """Return (start_angle_deg, span_deg) for segment i.

        In Qt: angles counter-clockwise from 3-o'clock.
        We want position 0 (C) at 12-o'clock, going clockwise.
        """
        start = 90 - i * 30 + 15  # +15 to center the 30° span
        span = -30                  # clockwise
        return start, span

    @staticmethod
    def _mid_angle_rad(i: int) -> float:
        """Angle in radians (math convention) for center of segment i."""
        return math.radians(90 - i * 30)

    @staticmethod
    def _point_at(cx, cy, r, angle_rad) -> QPointF:
        return QPointF(cx + r * math.cos(angle_rad), cy - r * math.sin(angle_rad))

    @staticmethod
    def _annular_path(cx, cy, outer_r, inner_r, start_deg, span_deg) -> QPainterPath:
        """QPainterPath for an annular sector (donut slice)."""
        outer_rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
        inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

        path = QPainterPath()
        path.arcMoveTo(outer_rect, start_deg)
        path.arcTo(outer_rect, start_deg, span_deg)
        end_deg = start_deg + span_deg
        path.arcTo(inner_rect, end_deg, -span_deg)
        path.closeSubpath()
        return path

    # -- Paint ---------------------------------------------------------------

    def paintEvent(self, event):
        cx, cy, max_r = self._geometry()
        outer_r = max_r
        mid_r = max_r * 0.72
        inner_r = max_r * 0.52
        center_r = max_r * 0.30

        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Background
            p.fillRect(self.rect(), QColor(COL_BG))

            # --- Progression arcs (behind segments) ---
            if self._progression and self._selected_pos is not None:
                self._draw_progression(p, cx, cy, outer_r, mid_r)

            # --- Major ring (outer) ---
            for i in range(12):
                self._draw_segment(
                    p, cx, cy, outer_r, mid_r, i,
                    CIRCLE_MAJOR_NAMES[i], ENHARMONIC_MAJOR.get(i),
                    is_minor=False,
                )

            # --- Minor ring (inner) ---
            for i in range(12):
                self._draw_segment(
                    p, cx, cy, mid_r, inner_r, i,
                    CIRCLE_MINOR_NAMES[i], ENHARMONIC_MINOR.get(i),
                    is_minor=True,
                )

            # --- Center info circle ---
            self._draw_center(p, cx, cy, center_r)

    def _segment_color(self, pos: int, is_minor: bool) -> str:
        """Determine fill color for a segment."""
        sel = self._selected_pos
        if self._active_segment == (pos, is_minor):
            return COL_ACTIVE_CHORD
        if sel is not None and pos == sel:
            if is_minor == self._selected_minor:
                return COL_SELECTED
            else:
                return COL_RELATIVE  # relative major/minor

        if (pos, is_minor) in self._diatonic_segments:
            return COL_MODE_HIGHLIGHT

        return COL_MINOR_SEG if is_minor else COL_MAJOR_SEG

    def _draw_segment(self, p: QPainter, cx, cy, outer_r, inner_r, i,
                       label, enharmonic_label, is_minor):
        start, span = self._segment_angles(i)
        color = self._segment_color(i, is_minor)

        path = self._annular_path(cx, cy, outer_r, inner_r, start, span)
        p.fillPath(path, QBrush(QColor(color)))
        p.strokePath(path, QPen(QColor(COL_BORDER), 1.5))

        # Text
        mid_a = self._mid_angle_rad(i)
        mid_rad = (outer_r + inner_r) / 2
        pt = self._point_at(cx, cy, mid_rad, mid_a)

        font_size = max(10, int(outer_r * 0.065))
        font = QFont("sans-serif", font_size, QFont.Weight.Bold)
        p.setFont(font)

        # Choose text color (dark on bright backgrounds)
        is_bright = color in (
            COL_SELECTED, COL_MODE_HIGHLIGHT, COL_RELATIVE, COL_ACTIVE_CHORD)
        p.setPen(QColor("#1a1a2e") if is_bright else QColor(COL_TEXT))

        text = label
        if enharmonic_label:
            text = f"{label}/{enharmonic_label}"

        fm = QFontMetricsF(font)
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        p.drawText(QRectF(pt.x() - tw / 2, pt.y() - th / 2, tw, th),
                    Qt.AlignmentFlag.AlignCenter, text)

        # Key signature (small, below label) — only on major ring
        if not is_minor:
            sharps, flats = KEY_SIGNATURES[i]
            if sharps and not flats:
                sig = f"{sharps}\u266f"
            elif flats and not sharps:
                sig = f"{flats}\u266d"
            elif sharps and flats:
                sig = f"{sharps}\u266f/{flats}\u266d"
            else:
                sig = ""
            if sig:
                small_font = QFont("sans-serif", max(8, int(outer_r * 0.04)))
                p.setFont(small_font)
                sfm = QFontMetricsF(small_font)
                sw = sfm.horizontalAdvance(sig)
                sh = sfm.height()
                offset = th * 0.5
                p.setPen(QColor("#1a1a2e") if is_bright else QColor(COL_TEXT_DIM))
                p.drawText(QRectF(pt.x() - sw / 2, pt.y() - sh / 2 + offset, sw, sh),
                            Qt.AlignmentFlag.AlignCenter, sig)

    def _draw_center(self, p: QPainter, cx, cy, r):
        """Draw the center info circle."""
        p.setBrush(QBrush(QColor(COL_CENTER_BG)))
        p.setPen(QPen(QColor(COL_BORDER), 2))
        p.drawEllipse(QPointF(cx, cy), r, r)

        if self._selected_pos is None:
            font = QFont("sans-serif", max(10, int(r * 0.25)))
            p.setFont(font)
            p.setPen(QColor(COL_TEXT_DIM))
            p.drawText(QRectF(cx - r, cy - r, r * 2, r * 2),
                        Qt.AlignmentFlag.AlignCenter, "Click\na key")
            return

        harmony = self._harmony
        if harmony is None:
            return
        name = harmony.chords[0].name

        # Key name (large)
        big = QFont("sans-serif", max(14, int(r * 0.45)), QFont.Weight.Bold)
        p.setFont(big)
        p.setPen(QColor(COL_SELECTED))
        p.drawText(QRectF(cx - r, cy - r * 0.6, r * 2, r * 0.6),
                    Qt.AlignmentFlag.AlignCenter, name)

        # Mode + quality (medium)
        med = QFont("sans-serif", max(9, int(r * 0.2)))
        p.setFont(med)
        p.setPen(QColor(COL_TEXT))
        mode_text = harmony.mode
        p.drawText(QRectF(cx - r, cy - r * 0.05, r * 2, r * 0.35),
                    Qt.AlignmentFlag.AlignCenter, mode_text)

        # Key signature (small)
        sig = harmony.signature_label

        small = QFont("sans-serif", max(8, int(r * 0.16)))
        p.setFont(small)
        p.setPen(QColor(COL_TEXT_DIM))
        p.drawText(QRectF(cx - r, cy + r * 0.25, r * 2, r * 0.35),
                    Qt.AlignmentFlag.AlignCenter, sig)

    def _draw_progression(self, p: QPainter, cx, cy, outer_r, mid_r):
        """Draw arcs connecting chord positions for the active progression."""
        prog = self._progression
        harmony = self._harmony
        if prog is None or harmony is None:
            return

        chords = prog.in_harmony(harmony)
        if len(chords) < 2:
            return

        pen = QPen(QColor(COL_PROGRESSION), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)

        for idx in range(len(chords) - 1):
            segment_a = circle_segment_for_chord(chords[idx])
            segment_b = circle_segment_for_chord(chords[idx + 1])
            if segment_a is None or segment_b is None:
                continue
            a, a_minor = segment_a
            b, b_minor = segment_b

            angle_a = self._mid_angle_rad(a)
            angle_b = self._mid_angle_rad(b)

            major_r = (outer_r + mid_r) / 2
            minor_r = mid_r * 0.86
            pt_a = self._point_at(cx, cy, minor_r if a_minor else major_r, angle_a)
            pt_b = self._point_at(cx, cy, minor_r if b_minor else major_r, angle_b)

            # Control point toward center for curved arc
            mid_x = (pt_a.x() + pt_b.x()) / 2
            mid_y = (pt_a.y() + pt_b.y()) / 2
            ctrl_x = cx + (mid_x - cx) * 0.4
            ctrl_y = cy + (mid_y - cy) * 0.4

            path = QPainterPath()
            path.moveTo(pt_a)
            path.quadTo(QPointF(ctrl_x, ctrl_y), pt_b)
            p.drawPath(path)

            # Arrowhead at destination
            self._draw_arrowhead(p, QPointF(ctrl_x, ctrl_y), pt_b, 10)

            # Step number at midpoint of curve
            t_x = 0.25 * pt_a.x() + 0.5 * ctrl_x + 0.25 * pt_b.x()
            t_y = 0.25 * pt_a.y() + 0.5 * ctrl_y + 0.25 * pt_b.y()
            num_font = QFont("sans-serif", max(8, int(outer_r * 0.04)), QFont.Weight.Bold)
            p.setFont(num_font)
            p.setPen(QColor(COL_PROGRESSION))
            p.drawText(QRectF(t_x - 10, t_y - 10, 20, 20),
                        Qt.AlignmentFlag.AlignCenter, str(idx + 1))
            p.setPen(pen)

    @staticmethod
    def _draw_arrowhead(p: QPainter, from_pt: QPointF, to_pt: QPointF, size: float):
        dx = to_pt.x() - from_pt.x()
        dy = to_pt.y() - from_pt.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        dx /= length
        dy /= length

        # Two points for the arrowhead
        px = -dy
        py = dx
        p1 = QPointF(to_pt.x() - dx * size + px * size * 0.4,
                      to_pt.y() - dy * size + py * size * 0.4)
        p2 = QPointF(to_pt.x() - dx * size - px * size * 0.4,
                      to_pt.y() - dy * size - py * size * 0.4)

        path = QPainterPath()
        path.moveTo(to_pt)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        p.fillPath(path, QBrush(QColor(COL_PROGRESSION)))

    # -- Mouse ---------------------------------------------------------------

    def mousePressEvent(self, event):
        cx, cy, max_r = self._geometry()
        outer_r = max_r
        mid_r = max_r * 0.72
        inner_r = max_r * 0.52

        dx = event.position().x() - cx
        dy = -(event.position().y() - cy)  # flip Y for math convention
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.degrees(math.atan2(dy, dx))

        # Convert angle to position (0-11)
        pos = round((90 - angle) / 30) % 12

        if mid_r <= dist <= outer_r:
            self._select(pos, minor=False)
        elif inner_r <= dist <= mid_r:
            self._select(pos, minor=True)
