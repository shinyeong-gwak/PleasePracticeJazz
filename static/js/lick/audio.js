const LickApp = window.LickApp || (window.LickApp = {
    state: {
        currentFile: null,
        savedLicks: {},
        playerLocked: false,
        playerLooped: false,
        grid: 8,
        activeLickId: null,
        selectedSavedLick: null
    },
    helpers: {},
    actions: {}
});

LickApp.helpers.getElement = function getElement(id) {
    return document.getElementById(id);
};

LickApp.helpers.showMessage = function showMessage(message) {
    const box = LickApp.helpers.getElement("messageBox");

    if (box) {
        box.innerText = message;
    }
};

LickApp.helpers.clearMessage = function clearMessage() {
    LickApp.helpers.showMessage("");
};

LickApp.helpers.formatTime = function formatTime(seconds) {
    if (!Number.isFinite(seconds)) {
        return "0:00";
    }

    const minutes = Math.floor(seconds / 60);
    const remainSeconds = Math.floor(seconds % 60);

    return `${minutes}:${remainSeconds.toString().padStart(2, "0")}`;
};

LickApp.helpers.getAudioElements = function getAudioElements() {
    return {
        audio: LickApp.helpers.getElement("audioPlayer"),
        seekBar: LickApp.helpers.getElement("seekBar"),
        currentTime: LickApp.helpers.getElement("currentTime"),
        duration: LickApp.helpers.getElement("duration"),
        tempo: LickApp.helpers.getElement("tempo"),
        tempoVal: LickApp.helpers.getElement("tempoVal"),
        pitch: LickApp.helpers.getElement("pitchVal"),
        lockButton: LickApp.helpers.getElement("lockPlayerBtn"),
        loopButton: LickApp.helpers.getElement("loopPlayerBtn")
    };
};

LickApp.helpers.updateLoopButton = function updateLoopButton() {
    const {audio, loopButton} = LickApp.helpers.getAudioElements();

    if (!audio || !loopButton) {
        return;
    }

    audio.loop = !!LickApp.state.playerLooped;
    loopButton.innerText = LickApp.state.playerLooped ? "🔂" : "🔁";
    loopButton.setAttribute(
        "aria-pressed",
        LickApp.state.playerLooped ? "true" : "false"
    );
    loopButton.setAttribute(
        "title",
        LickApp.state.playerLooped ? "반복 켜짐" : "반복 꺼짐"
    );
    loopButton.classList.toggle("is-active", LickApp.state.playerLooped);
};

LickApp.helpers.updateTempoLabel = function updateTempoLabel() {
    const {tempo, tempoVal} = LickApp.helpers.getAudioElements();

    if (tempo && tempoVal) {
        tempoVal.innerText = `${tempo.value}%`;
    }
};

LickApp.actions.playAudio = function playAudio() {
    const {audio} = LickApp.helpers.getAudioElements();

    if (audio) {
        audio.play();
    }
};

LickApp.actions.pauseAudio = function pauseAudio() {
    const {audio} = LickApp.helpers.getAudioElements();

    if (audio) {
        audio.pause();
    }
};

LickApp.actions.stopAudio = function stopAudio() {
    const {audio} = LickApp.helpers.getAudioElements();

    if (!audio) {
        return;
    }

    audio.pause();
    audio.currentTime = 0;
};

LickApp.actions.skip = function skip(seconds) {
    const {audio} = LickApp.helpers.getAudioElements();

    if (!audio) {
        return;
    }

    const nextTime = audio.currentTime + seconds;
    audio.currentTime = Math.max(0, Math.min(nextTime, audio.duration || nextTime));
};

LickApp.actions.togglePlayerLock = function togglePlayerLock() {
    const {audio, lockButton} = LickApp.helpers.getAudioElements();

    if (!audio || !lockButton) {
        return;
    }

    LickApp.state.playerLocked = !LickApp.state.playerLocked;
    audio.classList.toggle("player-fixed", LickApp.state.playerLocked);
    lockButton.innerText = LickApp.state.playerLocked ? "🔒" : "🔓";
};

LickApp.actions.togglePlayerLoop = function togglePlayerLoop() {
    const {audio} = LickApp.helpers.getAudioElements();

    if (!audio) {
        return;
    }

    LickApp.state.playerLooped = !LickApp.state.playerLooped;
    LickApp.helpers.updateLoopButton();
};

LickApp.actions.applyEffects = async function applyEffects() {
    if (!LickApp.state.currentFile) {
        return;
    }

    const {pitch, tempo, audio} = LickApp.helpers.getAudioElements();

    const payload = {
        file: LickApp.state.currentFile,
        pitch: parseInt(pitch.value, 10),
        tempo: parseInt(tempo.value, 10) / 100
    };

    const response = await fetch("/api/audio/process", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    audio.src = data.url;
    audio.play();
    LickApp.helpers.updateTempoLabel();
};

LickApp.actions.resetEffects = function resetEffects() {
    const {pitch, tempo} = LickApp.helpers.getAudioElements();

    pitch.value = "0";
    tempo.value = "100";
    LickApp.helpers.updateTempoLabel();

    LickApp.actions.applyEffects();
};

LickApp.actions.initAudio = function initAudio() {
    const {
        audio,
        seekBar,
        currentTime,
        duration,
        tempo,
        loopButton
    } = LickApp.helpers.getAudioElements();

    if (!audio || !seekBar || audio.dataset.initialized === "true") {
        return;
    }

    audio.dataset.initialized = "true";

    audio.addEventListener("loadedmetadata", () => {
        seekBar.max = Math.floor(audio.duration || 0);
        duration.innerText = LickApp.helpers.formatTime(audio.duration);
    });

    audio.addEventListener("timeupdate", () => {
        seekBar.value = audio.currentTime;
        currentTime.innerText = LickApp.helpers.formatTime(audio.currentTime);
        duration.innerText = LickApp.helpers.formatTime(audio.duration);
    });

    audio.addEventListener("ended", () => {
        if (!LickApp.state.playerLooped) {
            return;
        }

        audio.currentTime = 0;
        audio.play();
    });

    seekBar.addEventListener("input", () => {
        audio.currentTime = Number(seekBar.value);
    });

    tempo.addEventListener("input", LickApp.helpers.updateTempoLabel);
    loopButton?.addEventListener("click", event => {
        event.preventDefault();
        LickApp.actions.togglePlayerLoop();
    });
    LickApp.helpers.updateTempoLabel();
    LickApp.helpers.updateLoopButton();
};

window.playAudio = LickApp.actions.playAudio;
window.pauseAudio = LickApp.actions.pauseAudio;
window.stopAudio = LickApp.actions.stopAudio;
window.skip = LickApp.actions.skip;
window.applyEffects = LickApp.actions.applyEffects;
window.resetEffects = LickApp.actions.resetEffects;
window.togglePlayerLock = LickApp.actions.togglePlayerLock;
window.togglePlayerLoop = LickApp.actions.togglePlayerLoop;
