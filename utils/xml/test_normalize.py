from normalize import *

print(
    normalize_melody_tokens(
        ["D", "E", "G", "B"],
        "Bb"
    )
)

print(
    normalize_left_hand_tokens(
        ["C-E-G-Bb"],
        "C"
    )
)