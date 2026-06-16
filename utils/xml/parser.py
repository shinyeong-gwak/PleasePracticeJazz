# parser.py

import re

from models import (
    LeadSheet,
    Measure,
    NoteEvent,
)

from normalize import (
    normalize_melody_tokens,
    normalize_left_hand_tokens,
)

RHYTHM_TO_BEATS = {
    1: 4.0,
    2: 2.0,
    4: 1.0,
    8: 0.5,
    12: 1 / 3,
    16: 0.25,
    20: 0.2,
    24: 1 / 6,
    32: 0.125,
}


def measure_length(time_signature: str):

    if time_signature == "4/4":
        return 4.0

    if time_signature == "3/4":
        return 3.0

    raise ValueError(
        f"Unsupported time signature: {time_signature}"
    )


def split_measures(text: str):

    text = text.strip()

    if not text:
        return []

    parts = text.split("|")

    return [
        p.strip()
        for p in parts
        if p.strip()
    ]


def tokenize_measure(measure_text: str):

    if not measure_text:
        return []

    return measure_text.split()


def validate_rhythm_measure(
        rhythm_tokens,
        time_signature,
        is_pickup=False,
):

    total = 0

    for token in rhythm_tokens:

        value = int(token)

        if value not in RHYTHM_TO_BEATS:
            raise ValueError(
                f"Unsupported rhythm: {value}"
            )

        total += RHYTHM_TO_BEATS[value]

    if is_pickup:
        return

    expected = measure_length(
        time_signature
    )

    if abs(total - expected) > 0.0001:
        raise ValueError(
            f"Measure duration mismatch. "
            f"Expected={expected}, Actual={total}"
        )


def build_note_events(
        note_tokens,
        rhythm_tokens,
):

    if len(note_tokens) != len(rhythm_tokens):
        raise ValueError(
            f"Note count({len(note_tokens)}) "
            f"!= Rhythm count({len(rhythm_tokens)})"
        )

    events = []

    pending_tie = False

    for note, rhythm in zip(
            note_tokens,
            rhythm_tokens,
    ):

        rhythm = int(rhythm)

        if note == "!":

            events.append(
                NoteEvent(
                    notes=[],
                    rhythm=rhythm,
                    is_rest=True,
                )
            )

            continue

        tie_start = False
        tie_stop = False

        if note.endswith("~"):
            tie_start = True
            note = note[:-1]

        if pending_tie:
            tie_stop = True
            pending_tie = False

        if tie_start:
            pending_tie = True

        events.append(
            NoteEvent(
                notes=[note],
                rhythm=rhythm,
                tie_start=tie_start,
                tie_stop=tie_stop,
            )
        )

    return events


def build_left_hand_events(
        note_tokens,
        rhythm_tokens,
):

    if len(note_tokens) != len(rhythm_tokens):
        raise ValueError(
            f"LH note count mismatch"
        )

    events = []

    pending_tie = False

    for notes, rhythm in zip(
            note_tokens,
            rhythm_tokens,
    ):

        rhythm = int(rhythm)

        if notes == "!":

            events.append(
                NoteEvent(
                    notes=[],
                    rhythm=rhythm,
                    is_rest=True,
                )
            )

            continue

        tie_start = False
        tie_stop = False

        if pending_tie:
            tie_stop = True
            pending_tie = False

        events.append(
            NoteEvent(
                notes=notes,
                rhythm=rhythm,
                tie_start=tie_start,
                tie_stop=tie_stop,
            )
        )

    return events


def validate_chords(
        chord_tokens,
):

    count = len(chord_tokens)

    if count not in (1, 2, 4):
        raise ValueError(
            "Chord count per measure "
            "must be 1,2,or 4"
        )


def parse_lead_sheet(
        key_signature,
        time_signature,

        chord_text,

        rh_text,
        rh_rhythm_text,

        lh_text,
        lh_rhythm_text,
):

    chord_measures = split_measures(
        chord_text
    )

    rh_measures = split_measures(
        rh_text
    )

    rh_rhythm_measures = split_measures(
        rh_rhythm_text
    )

    lh_measures = split_measures(
        lh_text
    )

    lh_rhythm_measures = split_measures(
        lh_rhythm_text
    )

    measure_count = max(
        len(chord_measures),
        len(rh_measures),
        len(lh_measures),
    )

    measures = []

    for i in range(measure_count):

        chord_measure = (
            chord_measures[i]
            if i < len(chord_measures)
            else ""
        )

        rh_measure = (
            rh_measures[i]
            if i < len(rh_measures)
            else ""
        )

        rh_rhythm_measure = (
            rh_rhythm_measures[i]
            if i < len(rh_rhythm_measures)
            else ""
        )

        lh_measure = (
            lh_measures[i]
            if i < len(lh_measures)
            else ""
        )

        lh_rhythm_measure = (
            lh_rhythm_measures[i]
            if i < len(lh_rhythm_measures)
            else ""
        )

        chord_tokens = tokenize_measure(
            chord_measure
        )

        rh_tokens = tokenize_measure(
            rh_measure
        )

        rh_rhythm_tokens = tokenize_measure(
            rh_rhythm_measure
        )

        lh_tokens = tokenize_measure(
            lh_measure
        )

        lh_rhythm_tokens = tokenize_measure(
            lh_rhythm_measure
        )

        is_pickup = (
                i == 0 and
                not chord_text.strip().startswith("|")
        )

        validate_rhythm_measure(
            rh_rhythm_tokens,
            time_signature,
            is_pickup,
        )

        validate_rhythm_measure(
            lh_rhythm_tokens,
            time_signature,
            is_pickup,
        )

        if chord_tokens:
            validate_chords(
                chord_tokens
            )

        normalized_rh = (
            normalize_melody_tokens(
                rh_tokens,
                key_signature,
            )
        )

        normalized_lh = (
            normalize_left_hand_tokens(
                lh_tokens,
                key_signature,
            )
        )

        measure = Measure()

        measure.chords = chord_tokens

        measure.right_hand = (
            build_note_events(
                normalized_rh,
                rh_rhythm_tokens,
            )
        )

        measure.left_hand = (
            build_left_hand_events(
                normalized_lh,
                lh_rhythm_tokens,
            )
        )

        measure.is_pickup = is_pickup

        measures.append(
            measure
        )

    return LeadSheet(
        key_signature=key_signature,
        time_signature=time_signature,
        measures=measures,
    )