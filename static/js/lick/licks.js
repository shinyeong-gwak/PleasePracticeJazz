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

    audio.src = `/audio/lick/${file}`;
    audio.load();
};

LickPage.actions.init = function init() {
    LickPage.actions.initAudio();
    LickPage.helpers.updateSaveButton();
    LickPage.actions.loadSavedLicks();
};

window.selectLick = LickPage.actions.selectLick;

window.addEventListener("DOMContentLoaded", LickPage.actions.init);
