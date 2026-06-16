import re

NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
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

KEY_SIGNATURES = {
    "C": [],
    "G": ["F#"],
    "D": ["F#", "C#"],
    "A": ["F#", "C#", "G#"],
    "E": ["F#", "C#", "G#", "D#"],
    "B": ["F#", "C#", "G#", "D#", "A#"],
    "F#": ["F#", "C#", "G#", "D#", "A#", "E#"],

    "F": ["Bb"],
    "Bb": ["Bb", "Eb"],
    "Eb": ["Bb", "Eb", "Ab"],
    "Ab": ["Bb", "Eb", "Ab", "Db"],
    "Db": ["Bb", "Eb", "Ab", "Db", "Gb"],
    "Gb": ["Bb", "Eb", "Ab", "Db", "Gb", "Cb"],
}


RIGHT_LOW = 55   # G3
RIGHT_HIGH = 77  # F5

LEFT_LOW = 36    # C2
LEFT_HIGH = 69   # A4


def midi_to_note(midi: int, accidental_mode="flat"):

    octave = midi // 12 - 1
    semitone = midi % 12

    if accidental_mode == "sharp":
        note = SEMITONE_TO_SHARP[semitone]
    else:
        note = SEMITONE_TO_FLAT[semitone]

    return f"{note}{octave}"


def note_to_midi(note: str):

    m = re.match(r"^([A-Ga-g])([#bn]?)(\d+)$", note)

    if not m:
        raise ValueError(f"Invalid note: {note}")

    step = m.group(1).upper()
    accidental = m.group(2).lower()
    octave = int(m.group(3))

    if accidental == "n":
        accidental = ""

    pitch_name = step + accidental

    return (octave + 1) * 12 + NOTE_TO_SEMITONE[pitch_name]


def choose_nearest_pitch(
        pitch_class: int,
        previous_midi: int,
        low: int,
        high: int,
):

    candidates = []

    for octave in range(0, 10):

        midi = octave * 12 + pitch_class

        if low <= midi <= high:
            candidates.append(midi)

    if not candidates:
        raise ValueError(
            f"No note in range {low}~{high}"
        )

    return min(
        candidates,
        key=lambda x: abs(x - previous_midi)
    )


def apply_key_signature(
        note_name: str,
        key_signature: str,
):

    if note_name.endswith("n"):
        return note_name[:-1]

    if "#" in note_name or "b" in note_name:
        return note_name

    signature_notes = KEY_SIGNATURES.get(
        key_signature,
        []
    )

    for accidental_note in signature_notes:

        if accidental_note[0] == note_name:
            return accidental_note

    return note_name


def parse_note_token(
        token: str,
        key_signature: str,
):

    token = apply_key_signature(
        token,
        key_signature
    )

    m = re.match(
        r"^([A-Ga-g])([#bn]?)(\d+)?$",
        token
    )

    if not m:
        return None

    step = m.group(1).upper()
    accidental = m.group(2).lower()

    if accidental == "n":
        accidental = ""

    return NOTE_TO_SEMITONE[
        step + accidental
        ]