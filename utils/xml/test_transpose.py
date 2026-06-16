from parser import parse_lead_sheet
from transpose import generate_circle_of_fifths

sheet = parse_lead_sheet(
    key="Bb",
    time="4/4",

    chords="""
| CM7 CM7 F7 E7 |
""",

    rh="""
| D E G B F B G E |
""",

    rh_r="""
| 8 8 8 8 8 8 8 8 |
""",

    lh="""
| E-B-D |
""",

    lh_r="""
| 1 |
"""
)