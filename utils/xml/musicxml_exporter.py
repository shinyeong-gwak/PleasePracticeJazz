import re

from music21 import stream, note, chord, harmony, meter, key, tie, clef, layout, metadata, pitch as m21pitch

from data.model.models import LeadSheet
from utils.xml.music_theory import midi_to_note

RHYTHM_TO_Q = {
    1: 4.0,
    2: 2.0,
    4: 1.0,
    8: 0.5,
    12: 1 / 3,
    16: 0.25,
    20: 0.2,
    24: 1 / 6,
}

SHARP_KEYS = {"C", "G", "D", "A", "E", "B", "F#", "C#"}
FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb"}

SPECIAL_KEY_SPELLINGS = {
    "C#": {
        0: "B#",
        5: "E#",
    },
    "F#": {
        5: "E#",
    },
    "Db": {
        11: "Cb",
    },
}


def to_music21_chord(chord_name: str):

    match = re.match(
        r"^([A-Ga-g][b#]?)(.*?)(?:/([A-Ga-g][b#]?))?$",
        chord_name
    )

    if not match:
        return chord_name

    root = match.group(1)
    suffix = match.group(2)
    bass = match.group(3)

    mapping = {
        "M6": "6",
        "M69": "69",
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
    root = m21_note(root)
    result = root + suffix

    if bass:
        result += "/" + m21_note(bass)

    return result


def m21_note(note_name):

    if note_name.endswith("b"):
        return note_name[0].upper() + "-"

    if note_name.endswith("#"):
        return note_name[0].upper() + "#"

    return note_name.upper()


def get_measure_length(time_signature: str):

    top, bottom = time_signature.split("/")

    base_lengths = {
        "1": 4.0,
        "2": 2.0,
        "4": 1.0,
        "8": 0.5,
    }

    return int(top) * base_lengths[bottom]


def build_full_measure_rest(measure_length):

    rest = note.Rest()
    rest.quarterLength = measure_length
    rest.fullMeasure = True
    return rest


def get_accidental_mode_for_key(key_signature: str):

    if key_signature in SHARP_KEYS:
        return "sharp"

    if key_signature in FLAT_KEYS:
        return "flat"

    return "sharp"


def midi_to_spelled_pitch(midi_value, key_signature):

    accidental_mode = get_accidental_mode_for_key(
        key_signature
    )
    note_name = midi_to_note(
        midi_value,
        accidental_mode=accidental_mode
    )
    match = re.match(
        r"^([A-G][b#]?)(-?\d+)$",
        note_name
    )

    if not match:
        pitch = m21pitch.Pitch()
        pitch.midi = midi_value
        return pitch

    base_name = match.group(1)
    octave = int(match.group(2))
    special_map = SPECIAL_KEY_SPELLINGS.get(
        key_signature,
        {}
    )
    base_name = special_map.get(
        midi_value % 12,
        base_name
    )

    pitch = m21pitch.Pitch()
    pitch.name = base_name
    pitch.octave = octave

    while pitch.midi < midi_value:
        pitch.octave += 1

    while pitch.midi > midi_value:
        pitch.octave -= 1

    return pitch


def build_measure(events, measure_length, key_signature):

    measure = stream.Measure()

    if not events or all(event.is_rest for event in events):
        measure.append(build_full_measure_rest(measure_length))
        return measure

    for event in events:

        if event.is_rest:
            rest = note.Rest()
            rest.quarterLength = RHYTHM_TO_Q[event.rhythm]
            measure.append(rest)
            continue

        if len(event.notes) == 1:
            current_note = note.Note(
                midi_to_spelled_pitch(
                    event.notes[0],
                    key_signature
                )
            )
            current_note.quarterLength = RHYTHM_TO_Q[event.rhythm]

            if event.tie_start:
                current_note.tie = tie.Tie("start")

            if event.tie_stop:
                current_note.tie = tie.Tie("stop")

            measure.append(current_note)
            continue

        current_chord = chord.Chord([
            midi_to_spelled_pitch(
                midi_value,
                key_signature
            )
            for midi_value in event.notes
        ])
        current_chord.quarterLength = RHYTHM_TO_Q[event.rhythm]
        measure.append(current_chord)

    return measure


def add_harmony(measure, chords):

    if not chords:
        return

    beats_per = 4.0 / len(chords)
    offset = 0.0

    for name, count in chords:
        for _ in range(count):
            chord_symbol = harmony.ChordSymbol(to_music21_chord(name))
            measure.insert(offset, chord_symbol)
            offset += beats_per


def configure_part(part, part_name):

    part.partName = part_name
    part.partAbbreviation = ""


def build_piano_parts(score):

    rh_part = stream.PartStaff()
    lh_part = stream.PartStaff()

    configure_part(rh_part, "Piano")
    configure_part(lh_part, "Piano")

    staff_group = layout.StaffGroup(
        [rh_part, lh_part]
    )
    staff_group.symbol = "brace"
    staff_group.barTogether = True
    staff_group.name = "Piano"
    staff_group.abbreviation = "Pno."

    score.insert(0, staff_group)

    return rh_part, lh_part


def export_musicxml(sheet: LeadSheet, out_path: str, title: str = ""):

    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = (title or "").strip()

    key_signature = key.Key(sheet.key_signature)
    time_signature = meter.TimeSignature(sheet.time_signature)
    measure_length = get_measure_length(sheet.time_signature)

    rh_part, lh_part = build_piano_parts(score)

    for index, current_measure in enumerate(sheet.measures, start=1):

        rh_measure = build_measure(
            current_measure.right_hand,
            measure_length,
            sheet.key_signature
        )
        lh_measure = build_measure(
            current_measure.left_hand,
            measure_length,
            sheet.key_signature
        )

        rh_measure.number = index
        lh_measure.number = index

        add_harmony(rh_measure, current_measure.chords)

        if index == 1:
            rh_measure.insert(0, clef.TrebleClef())
            rh_measure.insert(0, key_signature)
            rh_measure.insert(0, time_signature)

            lh_measure.insert(0, clef.BassClef())
            lh_measure.insert(0, key_signature)
            lh_measure.insert(0, time_signature)

        rh_part.append(rh_measure)
        lh_part.append(lh_measure)

    score.insert(0, rh_part)
    score.insert(0, lh_part)
    score.write("musicxml", fp=out_path)

    return out_path


def export_circle_of_fifths_musicxml(scores, out_path, title: str = ""):

    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = (title or "").strip()

    rh_part, lh_part = build_piano_parts(score)

    measure_number = 1
    first = True

    for sheet in scores.values():

        key_signature = key.Key(sheet.key_signature)
        time_signature = meter.TimeSignature(sheet.time_signature)
        measure_length = get_measure_length(sheet.time_signature)

        for index, current_measure in enumerate(sheet.measures):

            rh_measure = build_measure(
                current_measure.right_hand,
                measure_length,
                sheet.key_signature
            )
            lh_measure = build_measure(
                current_measure.left_hand,
                measure_length,
                sheet.key_signature
            )

            rh_measure.number = measure_number
            lh_measure.number = measure_number
            measure_number += 1

            add_harmony(rh_measure, current_measure.chords)

            if index == 0:
                rh_measure.insert(0, clef.TrebleClef())
                rh_measure.insert(0, key_signature)
                rh_measure.insert(0, time_signature)

                lh_measure.insert(0, clef.BassClef())
                lh_measure.insert(0, key_signature)
                lh_measure.insert(0, time_signature)

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
