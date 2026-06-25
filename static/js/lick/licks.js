

const LickPage = window.LickApp || (window.LickApp = {
    state: {},
    helpers: {},
    actions: {}
});

LickPage.actions.selectLick = function selectLick(file) {
    const {audio} = LickPage.helpers.getAudioElements();

    LickPage.state.currentFile = file;
    LickPage.helpers.resetEditingState();
    LickPage.actions.closeLickModal();
    LickPage.actions.renderSavedLicks();

    document.querySelectorAll(".lick-item").forEach(item => {
        item.classList.toggle(
            "active",
            item.dataset.file === file
        );
    });

    audio.src = `/audio/lick/${file}`;
    audio.load();
};

LickPage.actions.init = function init() {
    LickPage.actions.initAudio();
    LickPage.helpers.updateSaveButton();
    LickPage.actions.loadSavedLicks();

    const selectedNode = document.getElementById("selected-lick-file-data");

    if (!selectedNode) {
        return;
    }

    try {
        const selectedFile = JSON.parse(selectedNode.textContent);

        if (selectedFile) {
            LickPage.actions.selectLick(selectedFile);
        }
    } catch (error) {
        console.error("selected lick parse error", error);
    }

};

window.selectLick = LickPage.actions.selectLick;

window.addEventListener("DOMContentLoaded", LickPage.actions.init);
