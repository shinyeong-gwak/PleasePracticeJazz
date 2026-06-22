const isMobile =
    /iPhone|iPad|iPod|Android/i.test(
        navigator.userAgent
    );

let activeInput = null;
let keyboard = null;
let activeCaret = 0;
let repeatTimer = null;
let repeatInterval = null;
let pianoMode = false;
let audioContext = null;
let keyboardMode = "general";

const MUSIC_INPUT_IDS = [
    "chordsInput",
    "melodyInput",
    "melodyRhythmInput",
    "degreesInput",
    "voicingInput",
    "voicingRhythmInput"
];

function isMusicInput(target) {
    return !!target && MUSIC_INPUT_IDS.includes(target.id);
}

function getMusicInput(target) {
    return target?.closest?.(
        "input, textarea"
    );
}

function isAudioControlTarget(target) {
    return !!target?.closest?.(
        "#audioPlayer, #seekBar, #lockPlayerBtn, .time-display"
    );
}

function updateKeyboardLayout() {
    if (!keyboard) {
        return;
    }

    keyboardMode =
        activeInput?.id === "chordsInput"
            ? "chord"
            : "general";

    keyboard
        .querySelectorAll(".kb-general-row")
        .forEach(row => {
            row.classList.toggle(
                "hidden",
                keyboardMode !== "general"
            );
        });

    keyboard
        .querySelectorAll(".kb-note-row")
        .forEach(row => {
            row.classList.toggle(
                "hidden",
                keyboardMode !== "general" || pianoMode
            );
        });

    keyboard
        .querySelectorAll(".kb-chord-row")
        .forEach(row => {
            row.classList.toggle(
                "hidden",
                keyboardMode !== "chord"
            );
        });
}

function showKeyboardFor(target) {
    if (!isMobile || !isMusicInput(target)) {
        return;
    }

    activeInput = target;
    activeCaret = target.value.length;

    if (keyboard) {
        keyboard.classList.add("show");
    }

    updateKeyboardLayout();

    target.readOnly = true;
    target.focus({preventScroll: true});

    try {
        target.setSelectionRange(
            activeCaret,
            activeCaret
        );
    } catch {
        // iOS readonly input/textarea can refuse caret updates.
    }

    window.setTimeout(() => {
        if (activeInput !== target) {
            return;
        }

        target.readOnly = false;
        target.setAttribute("inputmode", "none");

        try {
            target.setSelectionRange(
                activeCaret,
                activeCaret
            );
        } catch {
            // iOS can still refuse caret updates on some versions.
        }
    }, 0);
}

function hideKeyboard() {
    if (keyboard) {
        keyboard.classList.remove("show");
    }

    if (activeInput) {
        activeInput.readOnly = true;
        activeInput.blur();
    }

    activeInput = null;
    keyboardMode = "general";
}

function applyMobileInputMode(target) {
    target.readOnly = true;
    target.setAttribute("readonly", "readonly");
    target.setAttribute("inputmode", "none");
    target.setAttribute("autocapitalize", "off");
    target.setAttribute("autocomplete", "off");
    target.setAttribute("autocorrect", "off");
    target.setAttribute("spellcheck", "false");
}

function dispatchInputEvent(target) {
    target.dispatchEvent(
        new Event(
            "input",
            {bubbles: true}
        )
    );
}

function insertText(text) {
    if (!activeInput) {
        return;
    }

    const start = Math.max(
        0,
        Math.min(
            activeCaret,
            activeInput.value.length
        )
    );

    const end = start;

    const value =
        activeInput.value;

    let normalizedText = text;

    if (
        text === "-" &&
        start > 0 &&
        value[start - 1] === " "
    ) {
        activeInput.value =
            value.substring(0, start - 1)
            + value.substring(start);

        activeCaret = start - 1;
        return insertText("-");
    }

    activeInput.value =
        value.substring(0, start)
        + normalizedText
        + value.substring(end);

    const next =
        start + normalizedText.length;

    activeCaret = next;

    try {
        activeInput.setSelectionRange(
            next,
            next
        );
    } catch {
        // iOS readonly input/textarea can refuse caret updates.
    }

    dispatchInputEvent(activeInput);
    activeInput.focus({preventScroll: true});
}

function insertToken(token) {
    if (token === "!") {
        insertText(token);
        return;
    }

    insertText(token + " ");
}

function backspaceKey() {
    if (!activeInput) {
        return;
    }

    const start = Math.max(
        0,
        Math.min(
            activeCaret,
            activeInput.value.length
        )
    );

    if (start <= 0) {
        return;
    }

    const value =
        activeInput.value;

    const deleteFrom = start - 1;

    activeInput.value =
        value.substring(0, deleteFrom)
        + value.substring(start);

    activeCaret = deleteFrom;

    try {
        activeInput.setSelectionRange(
            deleteFrom,
            deleteFrom
        );
    } catch {
        // iOS readonly input/textarea can refuse caret updates.
    }

    dispatchInputEvent(activeInput);
    activeInput.focus({preventScroll: true});
}

function enterKey() {
    insertText("\n");
}

function spaceKey() {
    insertText(" ");
}

function moveCaret(delta) {
    if (!activeInput) {
        return;
    }

    activeCaret = Math.max(
        0,
        Math.min(
            activeInput.value.length,
            activeCaret + delta
        )
    );

    try {
        activeInput.focus({preventScroll: true});
        activeInput.setSelectionRange(
            activeCaret,
            activeCaret
        );
    } catch {
        // iOS readonly input/textarea can refuse caret updates.
    }
}

function moveCaretLeft() {
    moveCaret(-1);
}

function moveCaretRight() {
    moveCaret(1);
}

function getAudioContext() {
    if (!audioContext) {
        const AudioContextClass =
            window.AudioContext ||
            window.webkitAudioContext;

        if (!AudioContextClass) {
            return null;
        }

        audioContext = new AudioContextClass();
    }

    return audioContext;
}

function playPianoFrequency(frequency) {
    const context = getAudioContext();

    if (!context) {
        return;
    }

    if (context.state === "suspended") {
        context.resume();
    }

    const oscillator =
        context.createOscillator();
    const gainNode =
        context.createGain();

    oscillator.type = "triangle";
    oscillator.frequency.value =
        frequency;

    gainNode.gain.setValueAtTime(
        0.001,
        context.currentTime
    );
    gainNode.gain.exponentialRampToValueAtTime(
        0.18,
        context.currentTime + 0.01
    );
    gainNode.gain.exponentialRampToValueAtTime(
        0.001,
        context.currentTime + 0.35
    );

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    oscillator.start();
    oscillator.stop(context.currentTime + 0.36);
}

function playPianoNote(button) {
    const noteName =
        button.dataset.keyboardValue;
    const frequency =
        Number(button.dataset.pianoFrequency);

    insertText(noteName);
    playPianoFrequency(frequency);
}

function updatePianoMode() {
    if (!keyboard) {
        return;
    }

    keyboard.classList.toggle(
        "piano-mode",
        pianoMode
    );

    const piano =
        keyboard.querySelector("#pianoKeyboard");

    if (piano) {
        piano.classList.toggle(
            "hidden",
            !pianoMode
        );
    }

    updateKeyboardLayout();
}

function togglePianoMode() {
    pianoMode = !pianoMode;
    updatePianoMode();
}

function clearRepeatAction() {
    if (repeatTimer) {
        window.clearTimeout(repeatTimer);
        repeatTimer = null;
    }

    if (repeatInterval) {
        window.clearInterval(repeatInterval);
        repeatInterval = null;
    }
}

function startRepeatAction(button) {
    clearRepeatAction();

    if (button.dataset.repeatable !== "true") {
        return;
    }

    repeatTimer = window.setTimeout(() => {
        repeatInterval = window.setInterval(
            () => runButtonAction(button),
            70
        );
    }, 320);
}

function runButtonAction(button) {
    const action = button.dataset.keyboardAction;
    const value = button.dataset.keyboardValue ?? "";

    if (action === "insertText") {
        insertText(value);
        return;
    }

    if (action === "insertToken") {
        insertToken(value);
        return;
    }

    if (action === "playPianoNote") {
        playPianoNote(button);
        return;
    }

    if (action === "backspaceKey") {
        backspaceKey();
        return;
    }

    if (action === "moveCaretLeft") {
        moveCaretLeft();
        return;
    }

    if (action === "moveCaretRight") {
        moveCaretRight();
        return;
    }

    if (action === "spaceKey") {
        spaceKey();
        return;
    }

    if (action === "togglePianoMode") {
        togglePianoMode();
    }
}

function registerKeyboardButtons() {
    if (!keyboard) {
        return;
    }

    keyboard.addEventListener(
        "pointerdown",
        event => {
            const button =
                event.target.closest("button");

            if (
                !button ||
                !button.dataset.keyboardAction
            ) {
                return;
            }

            event.preventDefault();
            runButtonAction(button);
            startRepeatAction(button);
        }
    );

    keyboard.addEventListener(
        "pointerup",
        clearRepeatAction
    );

    keyboard.addEventListener(
        "pointerleave",
        clearRepeatAction
    );

    keyboard.addEventListener(
        "pointercancel",
        clearRepeatAction
    );
}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        keyboard =
            document.getElementById(
                "musicKeyboard"
            );

        registerKeyboardButtons();
        updatePianoMode();

        if (!isMobile) {
            return;
        }

        MUSIC_INPUT_IDS.forEach(id => {
            const target =
                document.getElementById(id);

            if (!target) {
                return;
            }

            applyMobileInputMode(target);
        });
    }
);

document.addEventListener(
    "pointerdown",
    event => {
        if (!isMobile) {
            return;
        }

        const input =
            getMusicInput(event.target);

        if (isMusicInput(input)) {
            event.preventDefault();
            showKeyboardFor(input);
            return;
        }

        const inKeyboard =
            event.target.closest(
                "#musicKeyboard"
            );

        if (isAudioControlTarget(event.target)) {
            return;
        }

        if (!inKeyboard) {
            hideKeyboard();
        }
    }
);

document.addEventListener(
    "focusin",
    event => {
        if (!isMobile) {
            return;
        }

        if (isMusicInput(event.target)) {
            showKeyboardFor(event.target);
            return;
        }

        const inKeyboard =
            event.target.closest?.(
                "#musicKeyboard"
            );

        if (isAudioControlTarget(event.target)) {
            return;
        }

        if (!inKeyboard) {
            hideKeyboard();
        }
    }
);

window.insertText = insertText;
window.insertToken = insertToken;
window.backspaceKey = backspaceKey;
window.spaceKey = spaceKey;
