from utils.xml.music_theory import (
    parse_note_token,
    choose_nearest_pitch,
    RIGHT_LOW,
    RIGHT_HIGH,
    LEFT_LOW,
    LEFT_HIGH, note_to_midi,
)
import re
from data.model.models import NormalizedToken


def _normalize(token, prev, key, low, high):

    # 옥타브가 지정된 경우
    if re.match(r"^[A-Ga-g][#bn]?\d+$", token):
        return note_to_midi(token)

    pc = parse_note_token(token, key)

    if pc is None:
        raise ValueError(token)

    return choose_nearest_pitch(
        pc,
        prev,
        low,
        high,
    )


# ---------------- RH ----------------

def normalize_melody_tokens(tokens, key):

    out = []
    prev = 72

    for t in tokens:

        if t == "!":
            out.append(NormalizedToken([], False, True))
            continue

        tie = False

        if t.endswith("~"):
            tie = True
            t = t[:-1]

        midi = _normalize(t, prev, key, RIGHT_LOW, RIGHT_HIGH)

        prev = midi

        out.append(NormalizedToken([midi], tie, False))

    return out


# ---------------- LH ----------------

def normalize_voicing(token, prev, key):

    notes = []
    cur = prev

    for n in token.split("-"):

        midi = _normalize(n, cur, key, LEFT_LOW, LEFT_HIGH)

        notes.append(midi)
        cur = midi

    return notes


def normalize_left_hand_tokens(tokens, key):

    out = []
    prev = 48

    for t in tokens:

        if t == "!":
            out.append(NormalizedToken([], False, True))
            continue

        tie = False

        if t.endswith("~"):
            tie = True
            t = t[:-1]

        voicing = normalize_voicing(t, prev, key)

        prev = voicing[-1]

        out.append(NormalizedToken(voicing, tie, False))

    return out