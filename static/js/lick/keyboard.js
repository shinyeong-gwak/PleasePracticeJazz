const isMobile =
    /iPhone|iPad|iPod|Android/i.test(
        navigator.userAgent
    );

let activeInput = null;
let keyboard = null;
let activeCaret = 0;

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

function showKeyboardFor(target) {
    if (!isMobile || !isMusicInput(target)) {
        return;
    }

    activeInput = target;
    activeCaret = target.value.length;

    if (keyboard) {
        keyboard.classList.add("show");
    }

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

    activeInput.value =
        value.substring(0, start)
        + text
        + value.substring(end);

    const next =
        start + text.length;

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

    if (action === "backspaceKey") {
        backspaceKey();
        return;
    }

    if (action === "enterKey") {
        enterKey();
        return;
    }

    if (action === "spaceKey") {
        spaceKey();
    }
}

function registerKeyboardButtons() {
    if (!keyboard) {
        return;
    }

    keyboard.querySelectorAll("button").forEach(button => {
        const rawHandler =
            button.getAttribute("onclick");

        if (!rawHandler) {
            return;
        }

        const insertTextMatch =
            rawHandler.match(
                /^insertText\('([\s\S]*)'\)$/
            );

        if (insertTextMatch) {
            button.dataset.keyboardAction =
                "insertText";
            button.dataset.keyboardValue =
                insertTextMatch[1];
        }

        const insertTokenMatch =
            rawHandler.match(
                /^insertToken\('([\s\S]*)'\)$/
            );

        if (insertTokenMatch) {
            button.dataset.keyboardAction =
                "insertToken";
            button.dataset.keyboardValue =
                insertTokenMatch[1];
        }

        if (rawHandler === "backspaceKey()") {
            button.dataset.keyboardAction =
                "backspaceKey";
        }

        if (rawHandler === "enterKey()") {
            button.dataset.keyboardAction =
                "enterKey";
        }

        if (rawHandler === "spaceKey()") {
            button.dataset.keyboardAction =
                "spaceKey";
        }

        button.removeAttribute("onclick");
    });

    keyboard.addEventListener(
        "pointerdown",
        event => {
            const button =
                event.target.closest("button");

            if (!button) {
                return;
            }

            event.preventDefault();
            runButtonAction(button);
        }
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

        if (!inKeyboard) {
            hideKeyboard();
        }
    }
);

window.insertText = insertText;
window.insertToken = insertToken;
window.backspaceKey = backspaceKey;
window.enterKey = enterKey;
window.spaceKey = spaceKey;
