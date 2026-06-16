from parser import parse_lead_sheet
from transpose import generate_circle_of_fifths

sheet = parse_lead_sheet(
    key_signature="Bb",
    time_signature="4/4",

    chord_text="""
| CM7 CM7 F7 E7 |
""",

    rh_text="""
| D E G B F B G E |
""",

    rh_rhythm_text="""
| 8 8 8 8 8 8 8 8 |
""",

    lh_text="""
| E-B-D |
""",

    lh_rhythm_text="""
| 1 |
"""
)

scores = generate_circle_of_fifths(sheet)

for key_name, score in scores.items():
    print(key_name)