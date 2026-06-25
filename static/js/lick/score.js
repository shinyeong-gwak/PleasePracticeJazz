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

const TREBLE_TOP = 72;
const BASS_TOP = 230;
const LINE_GAP = 11.7;
const BAR_PADDING_LEFT = 12;
const BASE_BAR_WIDTH = 180;
const MIN_NOTE_SPACING = 18;
const TREBLE_BOTTOM_DIATONIC = 4 * 7 + STAFF_INDEX.e;
const BASS_BOTTOM_DIATONIC = 2 * 7 + STAFF_INDEX.g;

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

LickScore.helpers.getDiatonicIndex = function getDiatonicIndex(note) {
    const parsed = LickScore.helpers.parseNote(note);

    if (!parsed) {
        return null;
    }

    return parsed.octave * 7 + STAFF_INDEX[parsed.letter];
};

LickScore.helpers.noteToY = function noteToY(note, staffType) {
    const diatonicIndex = LickScore.helpers.getDiatonicIndex(note);

    if (diatonicIndex === null) {
        return staffType === "bass" ? BASS_TOP : TREBLE_TOP;
    }

    const top = staffType === "bass" ? BASS_TOP : TREBLE_TOP;
    const bottomY = top + LINE_GAP * 4;
    const baseDiatonic = staffType === "bass"
        ? BASS_BOTTOM_DIATONIC
        : TREBLE_BOTTOM_DIATONIC;

    return bottomY - (diatonicIndex - baseDiatonic) * (LINE_GAP / 2);
};

LickScore.helpers.drawStaff = function drawStaff(ctx, width, top, label) {
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 1;

    for (let index = 0; index < 5; index += 1) {
        const y = top + index * LINE_GAP;

        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    ctx.fillStyle = "#4b5a55";
    ctx.font = "16px serif";
    ctx.fillText(label, 6, top - 12);
};

LickScore.helpers.countAccidentals = function countAccidentals(events) {
    return events
        .flat()
        .filter((note) => note.includes("#") || note.includes("b"))
        .length;
};

LickScore.helpers.buildBarLayouts = function buildBarLayouts(
    melodyBars,
    melodyRhythmBars,
    voicingBars,
    voicingRhythmBars
) {
    const grid = LickScore.helpers.getGrid();
    const layouts = [];
    let currentX = 0;
    const barCount = Math.max(
        melodyBars.length,
        melodyRhythmBars.length,
        voicingBars.length,
        voicingRhythmBars.length
    );

    for (let index = 0; index < barCount; index += 1) {
        const melodyBar = melodyBars[index] || [];
        const voicingBar = voicingBars[index] || [];
        const melodyCount = (melodyRhythmBars[index] || []).length || melodyBar.length;
        const voicingCount = (voicingRhythmBars[index] || []).length || voicingBar.length;
        const noteCount = Math.max(melodyCount, voicingCount, 1);
        const accidentalWidth =
            LickScore.helpers.countAccidentals(melodyBar.map((note) => [note]))
            + LickScore.helpers.countAccidentals(voicingBar);
        const width = BASE_BAR_WIDTH * Math.max(1, noteCount / grid) + accidentalWidth * 6;
        const spacing = Math.max(MIN_NOTE_SPACING, width / noteCount);

        layouts.push({
            startX: currentX,
            width,
            spacing
        });

        currentX += width;
    }

    return layouts;
};

LickScore.helpers.drawChordBlock = function drawChordBlock(ctx, layout, chordText) {
    if (!layout || !chordText) {
        return;
    }

    const chordParts = chordText.split(" ").filter(Boolean);

    if (chordParts.length >= 1) {
        ctx.fillText(chordParts[0], layout.startX + 10, 44);
    }

    if (chordParts.length >= 2) {
        ctx.fillText(chordParts[1], layout.startX + layout.width / 2, 44);
    }
};

LickScore.helpers.drawNoteHead = function drawNoteHead(ctx, x, y, accidental) {
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    if (accidental) {
        ctx.font = "14px serif";
        ctx.fillText(accidental === "b" ? "♭" : "♯", x - 12, y + 4);
    }
};

LickScore.helpers.drawMelodyBar = function drawMelodyBar(ctx, layout, bar) {
    let accidentalOffset = 0;

    bar.forEach((note, index) => {
        const parsed = LickScore.helpers.parseNote(note);
        const x = layout.startX + BAR_PADDING_LEFT + index * layout.spacing + accidentalOffset;
        const y = LickScore.helpers.noteToY(note, "treble");

        LickScore.helpers.drawNoteHead(
            ctx,
            x,
            y,
            parsed?.accidental
        );

        if (parsed?.accidental) {
            accidentalOffset += 5;
        }
    });
};

LickScore.helpers.drawVoicingBar = function drawVoicingBar(ctx, layout, bar) {
    bar.forEach((eventNotes, index) => {
        const x = layout.startX + BAR_PADDING_LEFT + index * layout.spacing;

        eventNotes.forEach((note, chordIndex) => {
            const parsed = LickScore.helpers.parseNote(note);
            const y = LickScore.helpers.noteToY(note, "bass");

            LickScore.helpers.drawNoteHead(
                ctx,
                x + chordIndex * 3,
                y,
                parsed?.accidental
            );
        });
    });
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
        const voicingRhythmBars = LickScore.helpers.getVoicingRhythmBars();
        const chords = LickScore.helpers.parseBarsKeepEmpty(
            LickScore.helpers.getElement("chordsInput").value
        );
        const layouts = LickScore.helpers.buildBarLayouts(
            melody,
            rhythmBars,
            voicing,
            voicingRhythmBars
        );
        const totalWidth = layouts.reduce((sum, layout) => sum + layout.width, 0);

        canvas.width = totalWidth + 50;
        canvas.height = 360;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#222";
        ctx.strokeStyle = "#333";
        ctx.font = "14px serif";

        LickScore.helpers.drawStaff(ctx, canvas.width, TREBLE_TOP, "RH");
        LickScore.helpers.drawStaff(ctx, canvas.width, BASS_TOP, "LH");

        layouts.forEach((layout) => {
            ctx.beginPath();
            ctx.moveTo(layout.startX, TREBLE_TOP - 12);
            ctx.lineTo(layout.startX, BASS_TOP + LINE_GAP * 4 + 18);
            ctx.stroke();
        });

        const lastLayout = layouts[layouts.length - 1];

        if (lastLayout) {
            ctx.beginPath();
            ctx.moveTo(lastLayout.startX + lastLayout.width, TREBLE_TOP - 12);
            ctx.lineTo(lastLayout.startX + lastLayout.width, BASS_TOP + LINE_GAP * 4 + 18);
            ctx.stroke();
        }

        chords.forEach((barChord, index) => {
            LickScore.helpers.drawChordBlock(
                ctx,
                layouts[index],
                barChord
            );
        });

        melody.forEach((bar, barIndex) => {
            const layout = layouts[barIndex];

            if (layout) {
                LickScore.helpers.drawMelodyBar(ctx, layout, bar);
            }
        });

        voicing.forEach((bar, barIndex) => {
            const layout = layouts[barIndex];

            if (layout) {
                LickScore.helpers.drawVoicingBar(ctx, layout, bar);
            }
        });
    } catch (error) {
        console.error(error);
        LickScore.helpers.showMessage(error.message);
    }
};

window.renderSequencer = LickScore.actions.renderSequencer;
window.renderScore = LickScore.actions.renderScore;
