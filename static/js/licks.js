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

function parseNote(note) {
    // d5, eb5, g#4
    const match = note.match(/([a-g])(#|b)?(\d)/i);
    if (!match) return null;

    let [, n, acc, oct] = match;

    let semitone = NOTE_MAP[n.toLowerCase()];

    if (acc === "#") semitone += 1;
    if (acc === "b") semitone -= 1;

    return {
        pitch: semitone + (parseInt(oct) * 12)
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
    const canvas = document.getElementById("scoreCanvas");
    const ctx = canvas.getContext("2d");

    const melody = parseMelody(document.getElementById("melodyInput").value);
    const voicing = parseVoicing(document.getElementById("voicingInput").value);
    const chords = document.getElementById("chordsInput").value.split("|").map(x => x.trim()).filter(Boolean);

    canvas.width = 1200;
    canvas.height = 400;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = 120;

    // ======================
    // 1. STAFF DRAW (오선)
    // ======================
    drawStaff(ctx, canvas.width);

    // ======================
    // 2. CHORDS
    // ======================
    ctx.fillStyle = "black";
    ctx.font = "14px monospace";

    chords.forEach((c, i) => {
        ctx.fillText(c, i * barWidth + 10, 50);
    });

    // ======================
    // 3. MELODY NOTES (STAFF 위)
    // ======================
    melody.forEach((bar, barIndex) => {
        bar.forEach((note, i) => {
            const x = barIndex * barWidth + i * NOTE_SPACING - 100;
            const y = noteToY(note);

            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    });

    // ======================
    // 4. VOICING (아래 영역)
    // ======================
    voicing.forEach((bar, barIndex) => {
        bar.forEach((note, i) => {
            const x = barIndex * barWidth + i * NOTE_SPACING;
            const y = 280;

            ctx.fillRect(x, y - (parseNote(note)?.pitch % 60), 6, 6);
        });
    });
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
const STEP_PER_SEMITONE = 3.25; // <- 핵심 (비율)

const BAR_WIDTH = 180;  // 기존 120 → 확대
const NOTE_SPACING = 14; // 10 → 확대

function noteToY(note) {
    if (!note) return STAFF_TOP;

    const midi = parseNote(note)?.pitch;
    if (!midi) return STAFF_TOP;

    const offset = (REFERENCE_MIDI - midi) * STEP_PER_SEMITONE;

    // staff 중심 기준선
    const centerLineY = STAFF_TOP + LINE_GAP * 2 + 33;

    return centerLineY + offset;
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