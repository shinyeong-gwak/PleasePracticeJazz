from music21 import stream, note, chord, harmony, meter, key, tie, clef, layout

from data.model.models import LeadSheet

import re

RHYTHM_TO_Q = {
    1: 4.0,
    2: 2.0,
    4: 1.0,
    8: 0.5,
    12: 1/3,
    16: 0.25,
    20: 0.2,
    24: 1/6,
}

def to_music21_chord(chord: str):

    m = re.match(r"^([A-Ga-g])([#b]?)(.*)$", chord)

    root = m.group(1).upper()
    accidental = m.group(2)
    suffix = m.group(3)

    mapping = {
        "M": "maj",
        "M7": "maj7",
        "M9": "maj9",
        "M11": "maj11",
        "M13": "maj13",

        "h7": "m7b5",

        "o": "dim",
        "o7": "dim7",

        "+": "aug",
        "+7": "aug7",
    }

    suffix = mapping.get(suffix, suffix)

    if accidental == "b":
        root += "-"
    elif accidental == "#":
        root += "#"

    return root + suffix

def build_measure(events):
    meas = stream.Measure()

    for e in events:

        if e.is_rest:
            r = note.Rest()
            r.quarterLength = RHYTHM_TO_Q[e.rhythm]
            meas.append(r)
            continue

        if len(e.notes) == 1:
            n = note.Note(e.notes[0])
            n.quarterLength = RHYTHM_TO_Q[e.rhythm]

            if e.tie_start:
                n.tie = tie.Tie("start")
            if e.tie_stop:
                n.tie = tie.Tie("stop")

            meas.append(n)

        else:
            c = chord.Chord(e.notes)
            c.quarterLength = RHYTHM_TO_Q[e.rhythm]
            meas.append(c)

    return meas


def add_harmony(measure, chords):
    if not chords:
        return

    beats_per = 4.0 / len(chords)
    offset = 0.0

    for name, count in chords:
        for _ in range(count):
            h = harmony.ChordSymbol(
                to_music21_chord(name)
            )
            measure.insert(offset, h)
            offset += beats_per




def export_musicxml(sheet: LeadSheet, out_path: str):

    score = stream.Score()

    ks = key.Key(sheet.key_signature)
    ts = meter.TimeSignature(sheet.time_signature)

    rh_part = stream.Part()
    lh_part = stream.Part()

    lh_part.insert(0, clef.BassClef())
    rh_part.insert(0, clef.TrebleClef())

    for m in sheet.measures:

        rh_measure = build_measure(m.right_hand)
        lh_measure = build_measure(m.left_hand)

        add_harmony(rh_measure, m.chords)

        rh_measure.insert(0, ks)
        rh_measure.insert(0, ts)

        lh_measure.insert(0, ks)
        lh_measure.insert(0, ts)

        rh_part.append(rh_measure)
        lh_part.append(lh_measure)

    score.insert(0, rh_part)
    score.insert(0, lh_part)

    score.write("musicxml", fp=out_path)

    return out_path

def export_circle_of_fifths_musicxml(scores, out_path):

    score = stream.Score()

    rh_part = stream.Part()
    lh_part = stream.Part()

    rh_part.insert(0, clef.TrebleClef())
    lh_part.insert(0, clef.BassClef())

    first = True

    for sheet in scores.values():

        ks = key.Key(sheet.key_signature)
        ts = meter.TimeSignature(sheet.time_signature)

        for i, m in enumerate(sheet.measures):

            rh_measure = build_measure(m.right_hand)
            lh_measure = build_measure(m.left_hand)

            add_harmony(rh_measure, m.chords)

            # 각 Key의 첫 마디에만 조표/박자표
            if i == 0:
                rh_measure.insert(0, ks)
                rh_measure.insert(0, ts)

                lh_measure.insert(0, ks)
                lh_measure.insert(0, ts)

                # 새 페이지에서 시작 (첫 곡 제외)
                if not first:
                    rh_measure.insert(0, layout.PageLayout(isNew=True))
                    lh_measure.insert(0, layout.PageLayout(isNew=True))

            rh_part.append(rh_measure)
            lh_part.append(lh_measure)

        first = False

    score.insert(0, rh_part)
    score.insert(0, lh_part)

    score.write("musicxml", fp=out_path)

    return out_path

# sheet = parse_lead_sheet(
#     key="Bb",
#     time="4/4",
#
#     chords="""
#     | Cm7 F7 | BbM7
#     """,
#
#     rh="""
#     | D F En D Eb F G5 A5 bb5 g5 Eb5 c5 d5 Bb4 G4 Eb4 | D4
#     """,
#
#     rh_r="""
#     | 16 16 16 16 16 16 16 16 16 16 16 16 16 16 16 16 | 4
#     """,
#
#     lh="""
#     | C2-Bb2 Eb3-A3 | Bb2-D3-A3 Bb2-D3-A3
#     """,
#
#     lh_r="""
#     | 4 !4 4 !4 | 4~ 8
#     """
# )
#
# scores = generate_circle_of_fifths(sheet)
#
# export_circle_of_fifths_musicxml(
#     scores,
#     "downloads/scores/circle_of_fifths.musicxml"
# )
#
# print("DONE")


# out = export_musicxml(
#     sheet,
#     "downloads/scores/test_output.musicxml"
# )
#
# print("DONE:", out)