const LickRhythm = window.LickApp || (window.LickApp = {
    state: {},
    helpers: {},
    actions: {}
});

LickRhythm.helpers.parseBarsKeepEmpty = function parseBarsKeepEmpty(input) {
    return input.split("|").map((bar) => bar.trim());
};

LickRhythm.helpers.parseBars = function parseBars(input) {
    return LickRhythm.helpers.parseBarsKeepEmpty(input).filter((bar) => bar.length > 0);
};

LickRhythm.helpers.parseMelodyBar = function parseMelodyBar(bar) {
    return bar.match(/[a-g](#|b)?\d/gi) || [];
};

LickRhythm.helpers.parseMelody = function parseMelody(input) {
    return LickRhythm.helpers.parseBarsKeepEmpty(input).map(LickRhythm.helpers.parseMelodyBar);
};

LickRhythm.helpers.parseVoicing = function parseVoicing(input) {
    return LickRhythm.helpers.parseBarsKeepEmpty(input).map((bar) => {
        if (!bar) {
            return [];
        }

        return bar.split("-").map((note) => note.trim()).filter(Boolean);
    });
};

LickRhythm.helpers.expandRhythmTokens = function expandRhythmTokens(tokens) {
    const result = [];

    for (const token of tokens) {
        if (token.startsWith("*")) {
            const repeatCount = parseInt(token.slice(1), 10);

            if (result.length === 0) {
                throw new Error("*N 앞에는 반드시 리듬값이 있어야 합니다.");
            }

            for (let index = 1; index < repeatCount; index += 1) {
                result.push(result[result.length - 1]);
            }

            continue;
        }

        result.push(token);
    }

    return result;
};

LickRhythm.helpers.buildDefaultRhythm = function buildDefaultRhythm(noteCount, grid) {
    if (noteCount > grid) {
        throw new Error(`음표 개수(${noteCount})가 Grid(${grid})보다 많습니다.`);
    }

    const notes = Array.from({length: noteCount}, () => String(grid));
    const rests = Array.from({length: grid - noteCount}, () => `!${grid}`);

    return [...notes, ...rests];
};

LickRhythm.helpers.getGrid = function getGrid() {
    const select = LickRhythm.helpers.getElement("gridSelect");
    const grid = parseInt(select.value, 10);

    LickRhythm.state.grid = grid;
    return grid;
};

LickRhythm.helpers.getRhythmBars = function getRhythmBars() {
    const grid = LickRhythm.helpers.getGrid();
    const melodyBars = LickRhythm.helpers.parseMelody(
        LickRhythm.helpers.getElement("melodyInput").value
    );
    const rhythmBars = LickRhythm.helpers.parseBarsKeepEmpty(
        LickRhythm.helpers.getElement("melodyRhythmInput").value
    );

    return melodyBars.map((melodyBar, index) => {
        const rhythmBar = rhythmBars[index] || "";

        if (!rhythmBar.trim()) {
            return LickRhythm.helpers.buildDefaultRhythm(melodyBar.length, grid);
        }

        return LickRhythm.helpers.expandRhythmTokens(
            rhythmBar.split(/\s+/).filter(Boolean)
        );
    });
};

LickRhythm.helpers.buildExportRhythm = function buildExportRhythm(notesInputId, rhythmInputId) {
    const rhythmRaw = LickRhythm.helpers.getElement(rhythmInputId).value.trim();

    if (rhythmRaw) {
        return rhythmRaw;
    }

    const grid = LickRhythm.helpers.getGrid();
    const bars = LickRhythm.helpers.parseBarsKeepEmpty(
        LickRhythm.helpers.getElement(notesInputId).value
    );

    const result = bars.map((bar) => {
        if (!bar.trim()) {
            return "";
        }

        const noteCount = bar.split(/\s+/).filter(Boolean).length;

        if (noteCount > grid) {
            throw new Error(`음표 개수(${noteCount})가 Grid(${grid})보다 많습니다.`);
        }

        const parts = [];

        if (noteCount > 0) {
            parts.push(`${grid} *${noteCount}`);
        }

        if (noteCount < grid) {
            parts.push(`!${grid} *${grid - noteCount}`);
        }

        return parts.join(" ");
    });

    return `| ${result.join(" | ")} |`;
};
