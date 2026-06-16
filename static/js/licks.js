let currentFile = null;


function selectLick(file) {
    currentFile = file;

    document.getElementById("metaBox").innerText = file;

    const audio = document.getElementById("audioPlayer");
    audio.src = `/audio/lick/${file}`;
    audio.load();
}


async function applyEffects() {
    if (!currentFile) return;

    const pitch = parseInt(document.getElementById("pitch").value);
    const tempo = parseInt(document.getElementById("tempo").value) / 100;

    document.getElementById("pitchVal").innerText = pitch;
    document.getElementById("tempoVal").innerText = tempo + "x";

    const res = await fetch("/api/audio/process", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            file: currentFile,
            pitch: pitch,
            tempo: tempo
        })
    });

    const data = await res.json();

    const audio = document.getElementById("audioPlayer");
    audio.src = data.url;
    audio.play();
}

const audio = document.getElementById("audioPlayer");
const seekBar = document.getElementById("seekBar");

audio.addEventListener("loadedmetadata", () => {
    seekBar.max = Math.floor(audio.duration);
});

audio.addEventListener("timeupdate", () => {
    seekBar.value = audio.currentTime;

    document.getElementById("currentTime").innerText =
        formatTime(audio.currentTime);

    document.getElementById("duration").innerText =
        formatTime(audio.duration);
});

seekBar.addEventListener("input", () => {
    audio.currentTime = seekBar.value;
});

function playAudio() {
    audio.play();
}

function pauseAudio() {
    audio.pause();
}

function stopAudio() {
    audio.pause();
    audio.currentTime = 0;
}

function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
}

const currentTimeEl = document.getElementById("currentTime");
const durationEl = document.getElementById("duration");

audio.addEventListener("timeupdate", () => {
    seekBar.value = audio.currentTime;

    if (currentTimeEl) {
        currentTimeEl.innerText = formatTime(audio.currentTime);
    }

    if (durationEl) {
        durationEl.innerText = formatTime(audio.duration);
    }
});

//===========
function parseBars(input) {
    return input
        .split("|")
        .map(bar => bar.trim())
        .filter(bar => bar.length > 0);
}

function parseNotes(bar) {
    // 16th note 기준 split (임시: 공백 없음 기준)
    return bar.match(/[a-g](#|b)?\d/g) || [];
}

function parseVoicing(bar) {
    // c5-eb5-g5 형태
    return bar.split("-").map(n => n.trim());
}

function countAccidentals(notes) {

    let count = 0;

    notes.forEach(note => {

        if (
            note.includes("#") ||
            note.includes("b")
        ) {
            count++;
        }
    });

    return count;
}

function renderSequencer() {
    const canvas = document.getElementById("sequencerCanvas");
    const ctx = canvas.getContext("2d");

    const chords = parseBars(document.getElementById("chordsInput").value);
    const melodyBars = parseBars(document.getElementById("melodyInput").value);
    const voicingBars = parseBars(document.getElementById("voicingInput").value);

    canvas.width = 1000;
    canvas.height = 300;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = BAR_WIDTH;
    const rowY = {
        chords: 50,
        melody: 130,
        voicing: 210
    };

    // GRID
    for (let i = 0; i < 20; i++) {
        ctx.strokeStyle = "#eee";
        ctx.beginPath();
        ctx.moveTo(i * 50, 0);
        ctx.lineTo(i * 50, 300);
        ctx.stroke();
    }

    // CHORDS
    chords.forEach((c, i) => {
        ctx.fillText(c, i * barWidth + 10, rowY.chords);
    });

    // MELODY
    melodyBars.forEach((bar, i) => {
        const notes = parseNotes(bar);
        ctx.fillText(notes.join(","), i * barWidth + 10, rowY.melody);
    });

    // VOICING
    voicingBars.forEach((bar, i) => {
        const notes = parseVoicing(bar);
        ctx.fillText(notes.join("-"), i * barWidth + 10, rowY.voicing);
    });
}

const NOTE_MAP = {
    c: 0,
    d: 2,
    e: 4,
    f: 5,
    g: 7,
    a: 9,
    b: 11
};

const STAFF_INDEX = {
    c: 0,
    d: 1,
    e: 2,
    f: 3,
    g: 4,
    a: 5,
    b: 6
};

function parseNote(note) {

    const match =
        note.match(
            /([a-g])(#|b)?(\d)/i
        );

    if (!match) {
        return null;
    }

    const [, letter, accidental, octave] =
        match;

    return {
        letter: letter.toLowerCase(),
        accidental: accidental || "",
        octave: parseInt(octave)
    };
}

function parseMelody(input) {
    return input.split("|").map(bar => {
        return bar.trim().match(/[a-g](#|b)?\d/g) || [];
    });
}

function parseVoicing(input) {
    return input.split("|").map(bar => {
        return bar.trim().split("-").map(n => n.trim());
    });
}

function renderScore() {

    updateGrid();

    const canvas = document.getElementById("scoreCanvas");
    const ctx = canvas.getContext("2d");

    const melody =
        parseMelody(
            document.getElementById("melodyInput").value
        );

    const voicing =
        parseVoicing(
            document.getElementById("voicingInput").value
        );

    const chords =
        document
            .getElementById("chordsInput")
            .value
            .split("|")
            .map(x => x.trim())
            .filter(Boolean);

    const layouts =
        buildBarLayouts(melody);

    const totalWidth =
        layouts.reduce(
            (sum, layout) => sum + layout.width,
            0
        );

    canvas.width = totalWidth + 50;
    canvas.height = 400;

    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    drawStaff(ctx, canvas.width);

    //--------------------------------------------------
    // 마디선
    //--------------------------------------------------

    layouts.forEach(layout => {

        ctx.beginPath();

        ctx.moveTo(layout.startX, 60);
        ctx.lineTo(layout.startX, 320);

        ctx.stroke();
    });

    //--------------------------------------------------
    // 마지막 마디선
    //--------------------------------------------------

    const lastLayout =
        layouts[layouts.length - 1];

    ctx.beginPath();

    ctx.moveTo(
        lastLayout.startX + lastLayout.width,
        60
    );

    ctx.lineTo(
        lastLayout.startX + lastLayout.width,
        320
    );

    ctx.stroke();

    //--------------------------------------------------
    // 코드
    //--------------------------------------------------

    chords.forEach((barChord, index) => {

        const layout = layouts[index];

        if (!layout) {
            return;
        }

        const chordParts =
            barChord
                .split(" ")
                .filter(Boolean);

        if (chordParts.length === 1) {

            ctx.fillText(
                chordParts[0],
                layout.startX + 10,
                50
            );
        }

        else if (chordParts.length === 2) {

            ctx.fillText(
                chordParts[0],
                layout.startX + 10,
                50
            );

            ctx.fillText(
                chordParts[1],
                layout.startX + layout.width / 2,
                50
            );
        }
    });

    //--------------------------------------------------
    // Melody
    //--------------------------------------------------

    melody.forEach((bar, barIndex) => {

        const layout =
            layouts[barIndex];

        bar.forEach((note, i) => {

            let accidentalOffset = 0;

            bar.forEach((note, i) => {

                const parsed =
                    parseNote(note);

                const x =
                    layout.startX +
                    BAR_PADDING_LEFT +
                    i * layout.spacing +
                    accidentalOffset;

                const y =
                    noteToY(note);

                ctx.beginPath();

                ctx.arc(
                    x,
                    y,
                    4,
                    0,
                    Math.PI * 2
                );

                ctx.fill();

                //----------------------------------
                // 임시표
                //----------------------------------

                if (parsed.accidental) {

                    ctx.font =
                        "14px serif";

                    ctx.fillText(
                        parsed.accidental === "b"
                            ? "♭"
                            : "♯",
                        x - 12,
                        y + 4
                    );

                    accidentalOffset += 5;
                }

            });

            const y =
                noteToY(note);

            ctx.beginPath();

            ctx.arc(
                x,
                y,
                4,
                0,
                Math.PI * 2
            );

            ctx.fill();
        });
    });

    //--------------------------------------------------
    // Voicing
    //--------------------------------------------------

    voicing.forEach((bar, barIndex) => {

        const layout =
            layouts[barIndex];

        bar.forEach((note, i) => {

            const x =
                layout.startX +
                BAR_PADDING_LEFT +
                i * layout.spacing;

            const y = 280;

            ctx.fillRect(
                x,
                y,
                6,
                6
            );
        });
    });
}

function buildBarLayouts(melodyBars) {

    const layouts = [];

    let currentX = 0;

    melodyBars.forEach(bar => {

        const noteCount = bar.length;

        const accidentalCount =
            countAccidentals(bar);

        const overflowRatio =
            Math.max(
                1,
                noteCount / GRID
            );

        const accidentalWidth =
            accidentalCount * 6;

        const width =
            BASE_BAR_WIDTH *
            overflowRatio +
            accidentalWidth;

        const spacing =
            Math.max(
                MIN_NOTE_SPACING,
                width / GRID
            );

        layouts.push({
            startX: currentX,
            width: width,
            spacing: spacing,
            accidentalCount: accidentalCount
        });

        currentX += width;
    });

    return layouts;
}

function drawStaff(ctx, width) {
    const startY = 80;
    const lineGap = 12;

    ctx.strokeStyle = "#333";
    ctx.lineWidth = 1;

    for (let i = 0; i < 5; i++) {
        const y = startY + i * lineGap;

        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
}
const STAFF_TOP = 80;
const LINE_GAP = 11.7;

// 기준 음 (middle C)
const REFERENCE_MIDI = 60; // C4
const STEP_PER_SEMITONE = 5.16; // <- 핵심 (비율)

const BAR_WIDTH = 180;  // 기존 120 → 확대
const NOTE_SPACING = 14; // 10 → 확대

const BAR_PADDING_LEFT = 6;

const BASE_BAR_WIDTH = 180;
const centerLineY =
    STAFF_TOP +
    LINE_GAP * 2 +
    207;


document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadSavedLicks();
    }
);

function noteToY(note) {

    const n = parseNote(note);

    if (!n) {
        return centerLineY;
    }

    const diatonicIndex =
        n.octave * 7 +
        STAFF_INDEX[n.letter];

    return (
        centerLineY -
        diatonicIndex * STEP_PER_SEMITONE
    );
}

function drawStaff(ctx, width) {
    const startY = STAFF_TOP;

    ctx.strokeStyle = "#333";
    ctx.lineWidth = 1;

    for (let i = 0; i < 5; i++) {
        const y = startY + i * LINE_GAP;

        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
}

let GRID = 8; // default
const MIN_NOTE_SPACING = 6;
function updateGrid() {
    const select = document.getElementById("gridSelect");
    GRID = parseInt(select.value);
}

function calcBarWidth(noteCount) {
    const spacing = Math.max(MIN_NOTE_SPACING, BASE_BAR_WIDTH / GRID);

    const requiredWidth = noteCount * spacing;

    return Math.max(BASE_BAR_WIDTH, requiredWidth);
}

function getNoteSpacing(barWidth) {
    return Math.max(MIN_NOTE_SPACING, barWidth / GRID);
}

function renderChords(ctx, chords, barWidth) {
    chords.forEach((c, i) => {

        const parts = c.split(" ").filter(x => x);

        if (parts.length === 1) {
            ctx.fillText(parts[0], i * barWidth + 10, 50);
        }

        if (parts.length === 2) {
            ctx.fillText(parts[0], i * barWidth + 10, 50);
            ctx.fillText(parts[1], i * barWidth + barWidth / 2, 50);
        }
    });
}

async function saveLick() {

    const payload = {

        file: currentFile,

        title:
        document.getElementById(
            "lickName"
        ).value,

        chords:
        document.getElementById(
            "chordsInput"
        ).value,

        degrees:
        document.getElementById(
            "degreesInput"
        ).value,

        melody:
        document.getElementById(
            "melodyInput"
        ).value,

        melodyRhythm:
        document.getElementById(
            "melodyRhythmInput"
        ).value,

        voicing:
        document.getElementById(
            "voicingInput"
        ).value,

        voicingRhythm:
        document.getElementById(
            "voicingRhythmInput"
        ).value
    };

    await fetch(
        "/music/licks/save",
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body:
                JSON.stringify(payload)
        }
    );

    loadSavedLicks();
}

let savedLicks = {};

async function loadSavedLicks() {

    const response =
        await fetch(
            "/music/licks/metadata"
        );

    savedLicks =
        await response.json();

    renderSavedLicks();
}

function renderSavedLicks() {

    const container =
        document.getElementById(
            "savedLicks"
        );

    container.innerHTML = "";

    if (!currentFile) {
        return;
    }

    const licks =
        savedLicks[currentFile] || [];

    licks.forEach((lick, index) => {

        const card =
            document.createElement("div");

        card.className =
            "saved-lick-card";

        card.innerHTML = `
            <div>
                <strong>
                    ${lick.title || "Untitled"}
                </strong>
            </div>

            <div>
                ${lick.chords || ""}
            </div>
        `;

        card.onclick =
            () => loadSavedLick(
                currentFile,
                index
            );

        container.appendChild(
            card
        );
    });
}

function loadSavedLick(
    fileName,
    index
) {

    const lick =
        savedLicks[fileName][index];

    document.getElementById(
        "lickName"
    ).value =
        lick.title || "";

    document.getElementById(
        "chordsInput"
    ).value =
        lick.chords || "";

    document.getElementById(
        "degreesInput"
    ).value =
        lick.degrees || "";

    document.getElementById(
        "melodyInput"
    ).value =
        lick.melody || "";

    document.getElementById(
        "melodyRhythmInput"
    ).value =
        lick.melodyRhythm || "";

    document.getElementById(
        "voicingInput"
    ).value =
        lick.voicing || "";

    document.getElementById(
        "voicingRhythmInput"
    ).value =
        lick.voicingRhythm || "";

    renderScore();
}