# normalize.py

from music_theory import (
    note_to_midi,
    choose_nearest_pitch,
    parse_note_token,
    RIGHT_LOW,
    RIGHT_HIGH,
    LEFT_LOW,
    LEFT_HIGH,
)


def _normalize_single_note(
        token: str,
        previous_midi: int,
        key_signature: str,
        low: int,
        high: int,
):

    pitch_class = parse_note_token(
        token,
        key_signature
    )

    if pitch_class is None:
        raise ValueError(
            f"Invalid note token: {token}"
        )

    midi = choose_nearest_pitch(
        pitch_class,
        previous_midi,
        low,
        high,
    )

    return midi


def normalize_melody_tokens(
        tokens: list[str],
        key_signature: str,
):

    result = []

    previous = 72  # C5

    for token in tokens:

        if token == "!":
            result.append("!")
            continue

        if "-" in token:
            raise ValueError(
                f"Chord/voicing token not allowed in RH: {token}"
            )

        midi = _normalize_single_note(
            token,
            previous,
            key_signature,
            RIGHT_LOW,
            RIGHT_HIGH,
        )

        previous = midi

        result.append(midi)

    return result


def normalize_voicing_token(
        token: str,
        previous_midi: int,
        key_signature: str,
):

    notes = token.split("-")

    result = []

    current_previous = previous_midi

    for note in notes:

        midi = _normalize_single_note(
            note,
            current_previous,
            key_signature,
            LEFT_LOW,
            LEFT_HIGH,
        )

        result.append(midi)

        current_previous = midi

    return result


def normalize_left_hand_tokens(
        tokens: list[str],
        key_signature: str,
):

    result = []

    previous = 48  # C3

    for token in tokens:

        if token == "!":
            result.append("!")
            continue

        voicing = normalize_voicing_token(
            token,
            previous,
            key_signature,
        )

        previous = voicing[-1]

        result.append(voicing)

    return result