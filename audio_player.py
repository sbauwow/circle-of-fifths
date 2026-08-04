"""Qt audio adapter for synthesized harmony previews."""

from __future__ import annotations

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices

from synth import synthesize_chord
from theory import Chord


class ChordAudioPlayer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sink: QAudioSink | None = None
        self._buffer: QBuffer | None = None

    def stop(self):
        if self._sink is not None:
            self._sink.stop()
            self._sink.deleteLater()
            self._sink = None
        if self._buffer is not None:
            self._buffer.close()
            self._buffer.deleteLater()
            self._buffer = None

    def play(self, chord: Chord) -> bool:
        self.stop()
        device = QMediaDevices.defaultAudioOutput()
        if device.isNull():
            return False

        audio_format = QAudioFormat()
        audio_format.setSampleRate(44_100)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        if not device.isFormatSupported(audio_format):
            return False

        pcm = synthesize_chord(chord.root.pitch_class, chord.pitch_classes)
        self._buffer = QBuffer(self)
        self._buffer.setData(QByteArray(pcm))
        self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)

        self._sink = QAudioSink(device, audio_format, self)
        self._sink.setVolume(0.72)
        self._sink.start(self._buffer)
        return True
