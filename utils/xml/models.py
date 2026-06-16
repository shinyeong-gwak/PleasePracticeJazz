from dataclasses import dataclass, field


@dataclass
class NoteToken:
    raw: str


@dataclass
class NoteEvent:
    notes: list[int]

    rhythm: int

    tie_start: bool = False
    tie_stop: bool = False

    is_rest: bool = False


@dataclass
class Measure:
    chords: list[str] = field(default_factory=list)

    right_hand: list[NoteEvent] = field(default_factory=list)
    left_hand: list[NoteEvent] = field(default_factory=list)

    is_pickup: bool = False


@dataclass
class LeadSheet:
    key_signature: str
    time_signature: str

    measures: list[Measure]