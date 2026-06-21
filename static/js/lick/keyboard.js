function insertText(text) {

    if (!activeInput) {
        return;
    }

    const start =
        activeInput.selectionStart;

    const end =
        activeInput.selectionEnd;

    const value =
        activeInput.value;

    activeInput.value =
        value.substring(0, start)
        + text
        + value.substring(end);

    activeInput.focus();

    activeInput.selectionStart =
        activeInput.selectionEnd =
            start + text.length;
}

function insertToken(token) {

    insertText(token + " ");
}

function backspaceKey() {

    if (!activeInput) {
        return;
    }

    const pos =
        activeInput.selectionStart;

    if (pos === 0) {
        return;
    }

    activeInput.value =
        activeInput.value.slice(0, pos - 1)
        + activeInput.value.slice(pos);

    activeInput.selectionStart =
        activeInput.selectionEnd =
            pos - 1;

    activeInput.focus();
}