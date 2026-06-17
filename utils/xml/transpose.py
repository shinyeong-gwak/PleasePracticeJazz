from copy import deepcopy

from data.model.models import (
    LeadSheet,
)

CIRCLE_OF_FIFTHS = [
    "C",
    "G",
    "D",
    "A",
    "E",
    "B",
    "F#",
    "Db",
    "Ab",
    "Eb",
    "Bb",
    "F",
]

KEY_TO_SEMITONE = {
    "C": 0,
    "Db": 1,
    "D": 2,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "G": 7,
    "Ab": 8,
    "A": 9,
    "Bb": 10,
    "B": 11,
}

import re

SEMITONE_TO_FLAT = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}

SEMITONE_TO_SHARP = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}

def transpose_pitch_name(
        pitch_name: str,
        semitones: int,
        accidental_mode="flat",
):

    pc = KEY_TO_SEMITONE[pitch_name]

    pc = (pc + semitones) % 12

    if accidental_mode == "sharp":
        return SEMITONE_TO_SHARP[pc]

    return SEMITONE_TO_FLAT[pc]

def transpose_chord_symbol(
        chord: str,
        semitones: int,
        accidental_mode="flat",
):

    m = re.match(
        r"^([A-Ga-g])([#b]?)(.*)$",
        chord
    )

    if not m:
        return chord

    root = m.group(1).upper() + m.group(2)
    suffix = m.group(3)

    if "/" in suffix:

        main_suffix, bass = suffix.split("/")

        bass = transpose_pitch_name(
            bass,
            semitones,
            accidental_mode,
        )

        return (
                transpose_pitch_name(
                    root,
                    semitones,
                    accidental_mode,
                )
                + main_suffix
                + "/"
                + bass
        )

    return (
            transpose_pitch_name(
                root,
                semitones,
                accidental_mode,
            )
            + suffix
    )

def transpose_lead_sheet(
        sheet: LeadSheet,
        semitones: int,
        target_key: str = None,
        accidental_mode="flat",
):

    result = deepcopy(sheet)

    if target_key:
        result.key_signature = target_key

    for measure in result.measures:

        measure.chords = [
            (
                transpose_chord_symbol(
                    chord_name,
                    semitones,
                    accidental_mode,
                ),
                count,
            )
            for chord_name, count in measure.chords
        ]

        for event in measure.right_hand:

            if event.is_rest:
                continue

            event.notes = [
                note + semitones
                for note in event.notes
            ]

        for event in measure.left_hand:

            if event.is_rest:
                continue

            event.notes = [
                note + semitones
                for note in event.notes
            ]

    return result

def generate_circle_of_fifths(
        sheet: LeadSheet,
        accidental_mode="flat",
):

    source_key = sheet.key_signature

    if source_key not in KEY_TO_SEMITONE:
        raise ValueError(
            f"Unsupported key: {source_key}"
        )

    source_pc = KEY_TO_SEMITONE[source_key]

    result = {}

    for target_key in CIRCLE_OF_FIFTHS:

        target_pc = KEY_TO_SEMITONE[target_key]

        diff = target_pc - source_pc

        score = transpose_lead_sheet(
            sheet,
            diff,
            target_key,
            accidental_mode,
        )

        result[target_key] = score

    return result