let selected = null;
let selectedFilename = null;
let osmd = null;

document.addEventListener("DOMContentLoaded", () => {
    const downloadButton = document.getElementById("downloadScoreButton");

    downloadButton.addEventListener("click", () => {
        if (!selectedFilename) {
            return;
        }

        window.location.href = `/score-download/${encodeURIComponent(selectedFilename)}`;
    });

    loadScores();
});

async function loadScores() {
    const res = await fetch("/score-list");
    const files = await res.json();

    const list = document.getElementById("scoreList");
    list.innerHTML = "";

    if (files.length === 0) {
        document.getElementById("output").innerHTML = "렌더할 MusicXML 파일이 없습니다.";
        return;
    }

    files.forEach((file) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "score-item";
        item.textContent = file.replace(/\.musicxml$/i, "");

        item.onclick = async () => {
            setActive(item, file);
            await renderScore(file);
        };

        list.appendChild(item);
    });
}

function setActive(item, filename) {
    const downloadButton = document.getElementById("downloadScoreButton");

    if (selected) {
        selected.classList.remove("active");
    }

    item.classList.add("active");
    selected = item;
    selectedFilename = filename;
    downloadButton.disabled = false;
}

function ensureOsmd(output) {
    if (!window.opensheetmusicdisplay) {
        throw new Error("OpenSheetMusicDisplay를 불러오지 못했습니다.");
    }

    if (!osmd) {
        osmd = new window.opensheetmusicdisplay.OpenSheetMusicDisplay(output, {
            autoResize: true,
            drawTitle: true,
            drawPartNames: false,
            backend: "svg"
        });
    } else {
        osmd.container = output;
    }

    return osmd;
}

async function renderScore(filename) {
    const output = document.getElementById("output");

    try {
        output.innerHTML = "악보를 렌더링하는 중입니다.";

        const res = await fetch(`/score-source/${encodeURIComponent(filename)}`);

        if (!res.ok) {
            throw new Error("MusicXML 파일을 불러오지 못했습니다.");
        }

        const xmlText = await res.text();
        output.innerHTML = "";

        const display = ensureOsmd(output);
        await display.load(xmlText);
        display.render();
    } catch (error) {
        console.error(error);
        output.innerHTML = `<div class="render-empty">${error.message}</div>`;
    }
}
