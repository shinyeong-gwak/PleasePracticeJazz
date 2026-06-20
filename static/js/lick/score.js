const LickScore = window.LickApp || (window.LickApp = {
    state: {},
    helpers: {},
    actions: {}
});

const STAFF_INDEX = {
    c: 0,
    d: 1,
    e: 2,
    f: 3,
    g: 4,
    a: 5,
    b: 6
};

const STAFF_TOP = 80;
const LINE_GAP = 11.7;
const STEP_PER_SEMITONE = 5.16;
const BAR_PADDING_LEFT = 6;
const BASE_BAR_WIDTH = 180;
const MIN_NOTE_SPACING = 6;
const CENTER_LINE_Y = STAFF_TOP + LINE_GAP * 2 + 207;

LickScore.helpers.parseNote = function parseNote(note) {
    const match = note.match(/([a-g])(#|b)?(\d)/i);

    if (!match) {
        return null;
    }

    const [, letter, accidental, octave] = match;

    return {
        letter: letter.toLowerCase(),
        accidental: accidental || "",
        octave: parseInt(octave, 10)
    };
};

LickScore.helpers.noteToY = function noteToY(note) {
    const parsed = LickScore.helpers.parseNote(note);

    if (!parsed) {
        return CENTER_LINE_Y;
    }

    const diatonicIndex = parsed.octave * 7 + STAFF_INDEX[parsed.letter];

    return CENTER_LINE_Y - diatonicIndex * STEP_PER_SEMITONE;
};

LickScore.helpers.drawStaff = function drawStaff(ctx, width) {
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 1;

    for (let index = 0; index < 5; index += 1) {
        const y = STAFF_TOP + index * LINE_GAP;

        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
};

LickScore.helpers.countAccidentals = function countAccidentals(notes) {
    return notes.filter((note) => note.includes("#") || note.includes("b")).length;
};

LickScore.helpers.buildBarLayouts = function buildBarLayouts(melodyBars, rhythmBars) {
    const grid = LickScore.helpers.getGrid();
    const layouts = [];
    let currentX = 0;

    melodyBars.forEach((bar, index) => {
        const noteCount = rhythmBars[index].length;
        const accidentalWidth = LickScore.helpers.countAccidentals(bar) * 6;
        const width = BASE_BAR_WIDTH * Math.max(1, noteCount / grid) + accidentalWidth;
        const spacing = Math.max(MIN_NOTE_SPACING, width / grid);

        layouts.push({
            startX: currentX,
            width: width,
            spacing: spacing
        });

        currentX += width;
    });

    return layouts;
};

LickScore.actions.renderSequencer = function renderSequencer() {
    const canvas = LickScore.helpers.getElement("sequencerCanvas");
    const ctx = canvas.getContext("2d");
    const chords = LickScore.helpers.parseBars(
        LickScore.helpers.getElement("chordsInput").value
    );
    const melodyBars = LickScore.helpers.parseBarsKeepEmpty(
        LickScore.helpers.getElement("melodyInput").value
    );
    const voicingBars = LickScore.helpers.parseBarsKeepEmpty(
        LickScore.helpers.getElement("voicingInput").value
    );
    const barWidth = BASE_BAR_WIDTH;
    const rowY = {
        chords: 50,
        melody: 130,
        voicing: 210
    };

    canvas.width = 1000;
    canvas.height = 300;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = "14px sans-serif";
    ctx.fillStyle = "#222";

    for (let index = 0; index < 20; index += 1) {
        ctx.strokeStyle = "#eee";
        ctx.beginPath();
        ctx.moveTo(index * 50, 0);
        ctx.lineTo(index * 50, 300);
        ctx.stroke();
    }

    chords.forEach((chord, index) => {
        ctx.fillText(chord, index * barWidth + 10, rowY.chords);
    });

    melodyBars.forEach((bar, index) => {
        const notes = LickScore.helpers.parseMelodyBar(bar);
        ctx.fillText(notes.join(","), index * barWidth + 10, rowY.melody);
    });

    voicingBars.forEach((bar, index) => {
        ctx.fillText(bar, index * barWidth + 10, rowY.voicing);
    });
};

LickScore.actions.renderScore = function renderScore() {
    try {
        LickScore.helpers.clearMessage();
        LickScore.helpers.getGrid();

        const canvas = LickScore.helpers.getElement("scoreCanvas");
        const ctx = canvas.getContext("2d");
        const melody = LickScore.helpers.parseMelody(
            LickScore.helpers.getElement("melodyInput").value
        );
        const voicing = LickScore.helpers.parseVoicing(
            LickScore.helpers.getElement("voicingInput").value
        );
        const rhythmBars = LickScore.helpers.getRhythmBars();
        const chords = LickScore.helpers.parseBars(
            LickScore.helpers.getElement("chordsInput").value
        );
        const layouts = LickScore.helpers.buildBarLayouts(melody, rhythmBars);
        const totalWidth = layouts.reduce((sum, layout) => sum + layout.width, 0);

        canvas.width = totalWidth + 50;
        canvas.height = 400;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#222";
        ctx.strokeStyle = "#333";
        ctx.font = "14px serif";

        LickScore.helpers.drawStaff(ctx, canvas.width);

        layouts.forEach((layout) => {
            ctx.beginPath();
            ctx.moveTo(layout.startX, 60);
            ctx.lineTo(layout.startX, 320);
            ctx.stroke();
        });

        const lastLayout = layouts[layouts.length - 1];

        if (lastLayout) {
            ctx.beginPath();
            ctx.moveTo(lastLayout.startX + lastLayout.width, 60);
            ctx.lineTo(lastLayout.startX + lastLayout.width, 320);
            ctx.stroke();
        }

        chords.forEach((barChord, index) => {
            const layout = layouts[index];

            if (!layout) {
                return;
            }

            const chordParts = barChord.split(" ").filter(Boolean);

            if (chordParts.length >= 1) {
                ctx.fillText(chordParts[0], layout.startX + 10, 50);
            }

            if (chordParts.length >= 2) {
                ctx.fillText(chordParts[1], layout.startX + layout.width / 2, 50);
            }
        });

        melody.forEach((bar, barIndex) => {
            const layout = layouts[barIndex];
            let accidentalOffset = 0;

            if (!layout) {
                return;
            }

            bar.forEach((note, index) => {
                const parsed = LickScore.helpers.parseNote(note);
                const x = layout.startX + BAR_PADDING_LEFT + index * layout.spacing + accidentalOffset;
                const y = LickScore.helpers.noteToY(note);

                ctx.beginPath();
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fill();

                if (parsed && parsed.accidental) {
                    ctx.font = "14px serif";
                    ctx.fillText(parsed.accidental === "b" ? "♭" : "♯", x - 12, y + 4);
                    accidentalOffset += 5;
                }
            });
        });

        voicing.forEach((bar, barIndex) => {
            const layout = layouts[barIndex];

            if (!layout) {
                return;
            }

            bar.forEach((note, index) => {
                const x = layout.startX + BAR_PADDING_LEFT + index * layout.spacing;
                const y = 280;

                if (note) {
                    ctx.fillRect(x, y, 6, 6);
                }
            });
        });
    } catch (error) {
        console.error(error);
        LickScore.helpers.showMessage(error.message);
    }
};

window.renderSequencer = LickScore.actions.renderSequencer;
window.renderScore = LickScore.actions.renderScore;
