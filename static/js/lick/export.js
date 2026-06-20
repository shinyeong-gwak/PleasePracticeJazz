const LickExport = window.LickApp || (window.LickApp = {
    state: {},
    helpers: {},
    actions: {}
});

LickExport.helpers.createPayload = function createPayload() {
    return {
        file: LickExport.state.currentFile,
        name: LickExport.helpers.getElement("lickName").value,
        key: LickExport.helpers.getElement("keyInput").value,
        time: LickExport.helpers.getElement("timeInput").value,
        chords: LickExport.helpers.getElement("chordsInput").value,
        rh: LickExport.helpers.getElement("melodyInput").value,
        rh_r: LickExport.helpers.buildExportRhythm("melodyInput", "melodyRhythmInput"),
        lh: LickExport.helpers.getElement("voicingInput").value,
        lh_r: LickExport.helpers.buildExportRhythm("voicingInput", "voicingRhythmInput")
    };
};

LickExport.helpers.exportMusicXmlByUrl = async function exportMusicXmlByUrl(url, successMessage) {
    try {
        LickExport.helpers.clearMessage();

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(LickExport.helpers.createPayload())
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "악보 생성에 실패했습니다.");
        }

        alert(`${successMessage}\n${result.path}`);
        window.location.href = `/music/licks/export-file?path=${encodeURIComponent(result.path)}`;
    } catch (error) {
        console.error(error);
        LickExport.helpers.showMessage(error.message);
    }
};

LickExport.actions.exportMusicXml = function exportMusicXml() {
    return LickExport.helpers.exportMusicXmlByUrl(
        "/music/licks/export",
        "생성 완료"
    );
};

LickExport.actions.export12KeysMusicXml = function export12KeysMusicXml() {
    return LickExport.helpers.exportMusicXmlByUrl(
        "/music/licks/export12",
        "12 Keys 생성 완료"
    );
};

window.exportMusicXml = LickExport.actions.exportMusicXml;
window.export12KeysMusicXml = LickExport.actions.export12KeysMusicXml;
