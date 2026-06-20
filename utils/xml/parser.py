from data.model.models import LeadSheet, Measure, NoteEvent
from utils.xml.normalize import (
    normalize_melody_tokens,
    normalize_left_hand_tokens,
)


RHYTHM = {
    1: 4.0,
    2: 2.0,
    4: 1.0,
    8: 0.5,
    12: 1/3,
    16: 0.25,
    20: 0.2,
    24: 1/6,
}

MEASURE_LENGTH = {
    "1": 4.0,
    "2": 2.0,
    "4": 1.0,
    "8": 0.5,
}

def get_measure_length(time_signature):

    top, bottom = time_signature.split("/")

    return int(top) * MEASURE_LENGTH[bottom]


def split_measures(text):
    text = text.strip()

    if not text:
        return []

    if "|" not in text:
        return [text]

    measures = [part.strip() for part in text.split("|")]

    if text.startswith("|"):
        measures = measures[1:]

    if text.endswith("|"):
        measures = measures[:-1]

    return measures


def validate(rh):

    total = 0

    for token in rh:
        rhythm, _ = parse_rhythm_token(token)
        total += RHYTHM[rhythm]

    return total


def compress(chords):

    if not chords:
        return []

    out = []
    prev = chords[0]
    c = 1

    for x in chords[1:]:

        if x == prev:
            c += 1
        else:
            out.append((prev, c))
            prev = x
            c = 1

    out.append((prev, c))
    return out

def expand_rhythm(tokens):

    result = []

    i = 0

    while i < len(tokens):

        token = tokens[i]

        # 20 *15
        if (
                i + 1 < len(tokens)
                and tokens[i + 1].startswith("*")
        ):

            count = int(
                tokens[i + 1][1:]
            )

            result.extend(
                [token] * count
            )

            i += 2

        else:

            result.append(token)
            i += 1

    return result

def parse_rhythm_token(token: str):

    is_rest = False

    if token.startswith("!"):
        is_rest = True
        token = token[1:]

    if token.endswith("~"):
        token = token[:-1]

    return int(token), is_rest

def build(events, rhythms, measure_length):

    out = []

    event_index = 0

    for token in rhythms:

        r, is_insert_rest = parse_rhythm_token(token)

        if is_insert_rest:
            out.append(
                NoteEvent([], r, False, False, True)
            )
            continue

        if event_index >= len(events):
            raise ValueError(
                "리듬보다 멜로디가 부족합니다."
            )

        t = events[event_index]
        event_index += 1

        if t.is_rest:

            out.append(
                NoteEvent([], r, False, False, True)
            )

        else:

            out.append(
                NoteEvent(
                    t.notes,
                    r,
                    t.tie_start,
                    False,
                    False,
                )
            )

    if event_index != len(events):
        raise ValueError(
            "멜로디와 리듬 개수가 맞지 않습니다."
        )

    for i in range(len(out) - 1):

        if out[i].tie_start:
            out[i + 1].tie_stop = True

    total = sum(
        RHYTHM[e.rhythm]
        for e in out
    )

    remain = measure_length - total

    if remain < -1e-6:
        raise ValueError("마디 길이를 초과했습니다.")

    while remain > 1e-6:

        for r in (1, 2, 4, 8, 12, 16, 20, 24):

            if RHYTHM[r] <= remain + 1e-6:

                out.append(
                    NoteEvent(
                        [],
                        r,
                        False,
                        False,
                        True,
                    )
                )

                remain -= RHYTHM[r]
                break

    return out

def parse_lead_sheet(
        *,
        key,
        time,
        chords,
        rh,
        rh_r,
        lh,
        lh_r,
):
    chords = split_measures(chords)
    rh = split_measures(rh)
    rh_r = split_measures(rh_r)
    lh = split_measures(lh)
    lh_r = split_measures(lh_r)

    mcount = max(
        len(chords),
        len(rh),
        len(rh_r),
        len(lh),
        len(lh_r)
    )

    measures = []

    for i in range(mcount):

        c = chords[i] if i < len(chords) else ""
        r = rh[i] if i < len(rh) else ""
        rr = rh_r[i] if i < len(rh_r) else ""
        l = lh[i] if i < len(lh) else ""
        lr = lh_r[i] if i < len(lh_r) else ""

        ct = c.split() if c else []
        rt = r.split() if r else []
        lt = l.split() if l else []
        rrt = expand_rhythm(
            rr.split()
        ) if rr else []

        lrt = expand_rhythm(
            lr.split()
        ) if lr else []

        validate(rrt)
        validate(lrt)

        ch = compress(ct)

        rn = normalize_melody_tokens(rt, key)
        ln = normalize_left_hand_tokens(lt, key)

        measure_length = get_measure_length(time)


        rh_events = build(
            rn,
            rrt,
            measure_length,
        )

        lh_events = build(
            ln,
            lrt,
            measure_length,
        )

        measures.append(
            Measure(
                chords=ch,
                right_hand=rh_events,
                left_hand=lh_events,
            )
        )

    return LeadSheet(key, time, measures)
