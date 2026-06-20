let selected = null;
let selectedFilename = null;

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
            await render(file);
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

async function render(filename) {
    const res = await fetch("/render", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({filename})
    });

    document.getElementById("output").innerHTML = await res.text();
}
