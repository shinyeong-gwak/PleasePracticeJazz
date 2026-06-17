from dataclasses import dataclass, field


@dataclass
class NormalizedToken:
    notes: list[int]
    tie_start: bool = False
    is_rest: bool = False


@dataclass
class NoteEvent:
    notes: list[int]
    rhythm: int
    tie_start: bool = False
    tie_stop: bool = False
    is_rest: bool = False


@dataclass
class Measure:
    chords: list
    right_hand: list[NoteEvent] = field(default_factory=list)
    left_hand: list[NoteEvent] = field(default_factory=list)
    is_pickup: bool = False


@dataclass
class LeadSheet:
    key_signature: str
    time_signature: str
    measures: list[Measure]