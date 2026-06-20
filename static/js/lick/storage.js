const LickStorage = window.LickApp || (window.LickApp = {
    state: {},
    helpers: {},
    actions: {}
});

LickStorage.helpers.getFormData = function getFormData() {
    return {
        id: LickStorage.state.activeLickId,
        file: LickStorage.state.currentFile,
        name: LickStorage.helpers.getElement("lickName").value,
        key: LickStorage.helpers.getElement("keyInput").value,
        time: LickStorage.helpers.getElement("timeInput").value,
        chords: LickStorage.helpers.getElement("chordsInput").value,
        degrees: LickStorage.helpers.getElement("degreesInput").value,
        melody: LickStorage.helpers.getElement("melodyInput").value,
        melodyRhythm: LickStorage.helpers.getElement("melodyRhythmInput").value,
        voicing: LickStorage.helpers.getElement("voicingInput").value,
        voicingRhythm: LickStorage.helpers.getElement("voicingRhythmInput").value
    };
};

LickStorage.helpers.updateSaveButton = function updateSaveButton() {
    const button = LickStorage.helpers.getElement("saveLickButton");

    if (!button) {
        return;
    }

    button.innerText = LickStorage.state.activeLickId ? "Update Lick" : "Save";
};

LickStorage.helpers.fillForm = function fillForm(lick) {
    LickStorage.helpers.getElement("lickName").value = lick.name || "";
    LickStorage.helpers.getElement("keyInput").value = lick.key || "C";
    LickStorage.helpers.getElement("timeInput").value = lick.time || "4/4";
    LickStorage.helpers.getElement("chordsInput").value = lick.chords || "";
    LickStorage.helpers.getElement("degreesInput").value = lick.degrees || "";
    LickStorage.helpers.getElement("melodyInput").value = lick.melody || "";
    LickStorage.helpers.getElement("melodyRhythmInput").value = lick.melodyRhythm || "";
    LickStorage.helpers.getElement("voicingInput").value = lick.voicing || "";
    LickStorage.helpers.getElement("voicingRhythmInput").value = lick.voicingRhythm || "";
};

LickStorage.helpers.resetEditingState = function resetEditingState() {
    LickStorage.state.activeLickId = null;
    LickStorage.helpers.updateSaveButton();
};

LickStorage.helpers.setEditingState = function setEditingState(lick) {
    LickStorage.state.activeLickId = lick.id || null;
    LickStorage.helpers.updateSaveButton();
};

LickStorage.helpers.renderModalContent = function renderModalContent(lick) {
    const body = LickStorage.helpers.getElement("lickModalBody");
    const title = LickStorage.helpers.getElement("lickModalTitle");

    title.innerText = lick.name || "Unnamed";
    body.innerHTML = `
        <div class="modal-meta-row"><strong>Key</strong><span>${lick.key || "C"}</span></div>
        <div class="modal-meta-row"><strong>Time</strong><span>${lick.time || "4/4"}</span></div>
        <div class="modal-meta-row"><strong>Chords</strong><span>${lick.chords || "-"}</span></div>
        <div class="modal-preview-block">
            <strong>Melody</strong>
            <pre>${lick.melody || "-"}</pre>
        </div>
        <div class="modal-preview-block">
            <strong>Voicing</strong>
            <pre>${lick.voicing || "-"}</pre>
        </div>
    `;
};

LickStorage.actions.openLickModal = function openLickModal(fileName, index) {
    const lick = (LickStorage.state.savedLicks[fileName] || [])[index];
    const modal = LickStorage.helpers.getElement("lickModal");

    if (!lick || !modal) {
        return;
    }

    LickStorage.state.selectedSavedLick = {
        fileName: fileName,
        index: index,
        lick: lick
    };

    LickStorage.helpers.renderModalContent(lick);
    modal.classList.remove("hidden");
};

LickStorage.actions.closeLickModal = function closeLickModal() {
    const modal = LickStorage.helpers.getElement("lickModal");

    LickStorage.state.selectedSavedLick = null;
    modal.classList.add("hidden");
};

LickStorage.actions.saveLick = async function saveLick() {
    if (!LickStorage.state.currentFile) {
        LickStorage.helpers.showMessage("먼저 MP3 파일을 선택해주세요.");
        return;
    }

    const response = await fetch("/music/licks/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(LickStorage.helpers.getFormData())
    });

    const result = await response.json();

    if (result.id) {
        LickStorage.state.activeLickId = result.id;
    }

    LickStorage.helpers.updateSaveButton();
    LickStorage.actions.loadSavedLicks();
};

LickStorage.actions.loadSavedLicks = async function loadSavedLicks() {
    const response = await fetch("/music/licks/metadata");
    LickStorage.state.savedLicks = await response.json();
    LickStorage.actions.renderSavedLicks();
};

LickStorage.actions.renderSavedLicks = function renderSavedLicks() {
    const metaBox = LickStorage.helpers.getElement("metaBox");
    const container = LickStorage.helpers.getElement("savedLicks");
    const currentFile = LickStorage.state.currentFile;

    metaBox.innerHTML = "";
    container.innerHTML = "";

    if (!currentFile) {
        metaBox.innerHTML = "<div class=\"saved-lick-empty\">파일을 선택하면 메타데이터가 표시됩니다.</div>";
        container.innerHTML = "<div class=\"saved-lick-empty\">저장된 Lick이 없습니다.</div>";
        return;
    }

    const title = document.createElement("div");
    title.className = "saved-lick-title";
    title.innerHTML = `<strong>${currentFile}</strong>`;
    metaBox.appendChild(title);

    const licks = LickStorage.state.savedLicks[currentFile] || [];

    if (licks.length === 0) {
        const empty = document.createElement("div");
        empty.className = "saved-lick-empty";
        empty.innerText = "저장된 Lick이 없습니다.";
        container.appendChild(empty);
        return;
    }

    licks.forEach((lick, index) => {
        const block = document.createElement("button");

        block.type = "button";
        block.className = "saved-lick-card";
        block.innerHTML = `
            <div class="saved-lick-card-header">
                <strong>${lick.name || "Unnamed"}</strong>
                ${lick.id === LickStorage.state.activeLickId ? "<span class='saved-lick-badge'>editing</span>" : ""}
            </div>
            <div>${lick.key || "C"} / ${lick.time || "4/4"}</div>
        `;
        block.addEventListener("click", () => {
            LickStorage.actions.openLickModal(currentFile, index);
        });

        container.appendChild(block);
    });
};

LickStorage.actions.loadSavedLick = function loadSavedLick(fileName, index) {
    const lick = (LickStorage.state.savedLicks[fileName] || [])[index];

    if (!lick) {
        return;
    }

    LickStorage.helpers.fillForm(lick);
    LickStorage.actions.renderScore();
};

LickStorage.actions.loadSelectedSavedLick = function loadSelectedSavedLick() {
    const selected = LickStorage.state.selectedSavedLick;

    if (!selected) {
        return;
    }

    LickStorage.actions.loadSavedLick(selected.fileName, selected.index);
    LickStorage.actions.closeLickModal();
};

LickStorage.actions.editSelectedSavedLick = function editSelectedSavedLick() {
    const selected = LickStorage.state.selectedSavedLick;

    if (!selected) {
        return;
    }

    LickStorage.actions.loadSavedLick(selected.fileName, selected.index);
    LickStorage.helpers.setEditingState(selected.lick);
    LickStorage.actions.renderSavedLicks();
    LickStorage.actions.closeLickModal();
};

LickStorage.actions.deleteSelectedSavedLick = async function deleteSelectedSavedLick() {
    const selected = LickStorage.state.selectedSavedLick;

    if (!selected) {
        return;
    }

    await fetch(
        `/music/licks/${encodeURIComponent(selected.fileName)}/${encodeURIComponent(selected.lick.id)}`,
        {method: "DELETE"}
    );

    if (LickStorage.state.activeLickId === selected.lick.id) {
        LickStorage.helpers.resetEditingState();
    }

    LickStorage.actions.closeLickModal();
    LickStorage.actions.loadSavedLicks();
};

window.saveLick = LickStorage.actions.saveLick;
window.loadSavedLicks = LickStorage.actions.loadSavedLicks;
window.closeLickModal = LickStorage.actions.closeLickModal;
window.loadSelectedSavedLick = LickStorage.actions.loadSelectedSavedLick;
window.editSelectedSavedLick = LickStorage.actions.editSelectedSavedLick;
window.deleteSelectedSavedLick = LickStorage.actions.deleteSelectedSavedLick;
