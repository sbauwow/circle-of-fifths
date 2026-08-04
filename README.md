# Circle of Fifths

A guitar-focused PySide6 harmony explorer. Select a major or minor key on the
circle, change modes, inspect correctly spelled diatonic chords, and project a
scale or selected chord onto the fretboard.

## Download

Standalone desktop builds are published on the
[GitHub Releases](https://github.com/sbauwow/circle-of-fifths/releases) page.
Linux, Windows, and macOS packages are attached to each versioned release.

## Run

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Click a chord below the circle to hear it and isolate its tones on the circle
and fretboard. Click the selected chord again to return to the complete scale.
The CAGED overlay is available for standard-interval tunings; straight-bar
slide positions are available for open and modal tunings. Enable Capo and
choose a physical fret to see concert-pitch notes above the capo; the string
labels update to show the new sounding open notes.

## Test

```sh
python -m unittest discover -s test -v
```

The theory engine and PCM synthesizer have no Qt dependency, so their tests can
also run with the system Python before PySide6 is installed.
