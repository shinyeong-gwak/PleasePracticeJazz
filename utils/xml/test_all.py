from parser import parse_lead_sheet
from transpose import generate_circle_of_fifths
from musicxml_exporter import export_musicxml

sheet = parse_lead_sheet(
    key="Bb",
    time="4/4",

    chords="""
| BbM7 Cm7 F7 |
""",

    rh="""
| D F A C5 |
""",

    rh_r="""
| 4 4 4 4 |
""",

    lh="""
| Bb-D-F |
""",

    lh_r="""
| 1 |
"""
)

scores = generate_circle_of_fifths(sheet)

for key_name, score in scores.items():

    out = f"downloads/scores/{key_name}.musicxml"

    export_musicxml(score, out)

    print(out)