const ClipBrowser = (() => {
    let tree = null;
    let selectedFilePath = "";
    let selectedFolderPath = "";
    let sortMode = "name-asc";
    const collapsedFolders = new Set();

    function node(path) {
        return document.querySelector(path);
    }

    function fileSelect() {
        return document.getElementById("fileSelect");
    }

    function normalizeChildren(children = []) {
        const sorted = [...children];
        sorted.sort((a, b) => {
            if (sortMode === "folder-first") {
                const typeCompare = Number(a.type !== "folder") - Number(b.type !== "folder");
                if (typeCompare !== 0) return typeCompare;
            }

            const direction = sortMode === "name-desc" ? -1 : 1;
            return a.name.localeCompare(b.name, "ko") * direction;
        });
        return sorted;
    }

    function flattenFiles(current = tree, files = []) {
        if (!current) return files;
        if (current.type === "file") {
            files.push(current.path);
            return files;
        }
        (current.children || []).forEach((child) => flattenFiles(child, files));
        return files;
    }

    function syncSelectOptions() {
        const select = fileSelect();
        if (!select) return;

        const files = flattenFiles();
        select.innerHTML = "";
        files.forEach((path) => {
            const option = document.createElement("option");
            option.value = path;
            option.textContent = path;
            select.appendChild(option);
        });

        if (!selectedFilePath && files.length) {
            selectedFilePath = files[0];
        }
        select.value = selectedFilePath;
        syncSelectedLabel();
    }

    function syncSelectedLabel() {
        const label = node("[data-audio-selected-label]");
        if (label) {
            label.textContent = selectedFilePath || "선택된 음원이 없어요";
        }
    }

    function makeTreeRow(item, depth) {
        const row = document.createElement("button");
        row.type = "button";
        row.className = `audio-tree-row audio-tree-${item.type}`;
        row.style.setProperty("--depth", depth);
        row.dataset.path = item.path;
        row.dataset.type = item.type;

        if (item.type === "file" && item.path === selectedFilePath) {
            row.classList.add("is-selected");
        }
        if (item.type === "folder" && item.path === selectedFolderPath) {
            row.classList.add("is-folder-selected");
        }

        const icon = document.createElement("span");
        icon.className = "audio-tree-icon";
        icon.textContent = item.type === "folder"
            ? (collapsedFolders.has(item.path) ? "▸" : "▾")
            : "♪";

        const name = document.createElement("span");
        name.className = "audio-tree-name";
        name.textContent = item.name;

        row.append(icon, name);

        row.addEventListener("click", () => {
            if (item.type === "folder") {
                selectedFolderPath = item.path;
                if (collapsedFolders.has(item.path)) {
                    collapsedFolders.delete(item.path);
                } else {
                    collapsedFolders.add(item.path);
                }
                renderTree();
                return;
            }

            selectFile(item.path);
            loadAudio();
        });

        return row;
    }

    function renderNode(item, depth, container) {
        container.appendChild(makeTreeRow(item, depth));
        if (item.type !== "folder" || collapsedFolders.has(item.path)) {
            return;
        }

        normalizeChildren(item.children).forEach((child) => {
            renderNode(child, depth + 1, container);
        });
    }

    function renderTree() {
        const container = node("[data-audio-tree]");
        if (!container) return;

        container.innerHTML = "";
        if (!tree) {
            container.textContent = "음원을 불러오는 중이에요.";
            return;
        }

        normalizeChildren(tree.children).forEach((child) => {
            renderNode(child, 0, container);
        });

        if (!tree.children?.length) {
            container.innerHTML = '<div class="audio-tree-empty">downloads/mp3 안에 MP3 파일을 넣어주세요.</div>';
        }
    }

    function selectFile(path) {
        selectedFilePath = path;
        const select = fileSelect();
        if (select) select.value = path;
        syncSelectedLabel();
        renderTree();
    }

    async function readJsonResponse(response) {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.message || "요청을 처리하지 못했어요.");
        }
        return data;
    }

    async function refreshTree(nextTree = null) {
        tree = nextTree || await readJsonResponse(await fetch("/music/clips/tree"));
        syncSelectOptions();
        renderTree();
    }

    function showTreeError(error) {
        const container = node("[data-audio-tree]");
        if (container) {
            container.innerHTML = `<div class="audio-tree-empty">${error.message || "음원을 불러오지 못했어요."}</div>`;
        }
    }

    function selectedFolderOrRoot() {
        return selectedFolderPath || "";
    }

    async function mutateFolder(method, body) {
        const response = await fetch("/music/clips/folders", {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        return readJsonResponse(response);
    }

    function bindFolderMenu() {
        const toggle = node("[data-folder-menu-toggle]");
        const menu = node("[data-folder-menu]");
        const nameInput = node("[data-folder-name]");
        const status = node("[data-folder-status]");
        const sortSelect = node("[data-audio-sort]");
        const createButton = node("[data-folder-create]");
        const renameButton = node("[data-folder-rename]");
        const deleteButton = node("[data-folder-delete]");

        toggle?.addEventListener("click", () => {
            if (menu) {
                menu.hidden = !menu.hidden;
                menu.classList.toggle("is-open", !menu.hidden);
            }
        });

        sortSelect?.addEventListener("change", () => {
            sortMode = sortSelect.value;
            renderTree();
        });

        const run = async (action) => {
            if (status) status.textContent = "";
            try {
                const nextTree = await action();
                await refreshTree(nextTree);
                if (status) status.textContent = "반영했어요.";
                if (nameInput) nameInput.value = "";
            } catch (error) {
                if (status) status.textContent = error.message;
            }
        };

        createButton?.addEventListener("click", () => run(() => mutateFolder("POST", {
            parentPath: selectedFolderOrRoot(),
            name: nameInput.value,
        })));

        renameButton?.addEventListener("click", () => run(() => mutateFolder("PUT", {
            path: selectedFolderPath,
            name: nameInput.value,
        })));

        deleteButton?.addEventListener("click", () => {
            if (!selectedFolderPath) {
                if (status) status.textContent = "삭제할 폴더를 선택해주세요.";
                return;
            }
            run(() => mutateFolder("DELETE", { path: selectedFolderPath }));
        });
    }

    function init() {
        bindFolderMenu();
        void refreshTree().catch(showTreeError);
    }

    return {
        init,
        selectFile,
        getSelectedFilePath: () => selectedFilePath || fileSelect()?.value || "",
    };
})();

window.ClipBrowser = ClipBrowser;

function loadAudio() {
    const fileName = ClipBrowser.getSelectedFilePath();
    const player = document.getElementById("player");

    if (!fileName || !player) {
        return;
    }

    player.src = "/music/audio/" + encodeURIComponent(fileName).replace(/%2F/g, "/");
    player.load();
}

function formatTime(seconds) {
    const min = Math.floor(seconds / 60);
    const sec = (seconds % 60).toFixed(2).padStart(5, "0");
    return `${min}:${sec}`;
}

function parseTime(text) {
    const value = String(text || "").trim();
    if (!value) return 0;
    if (!value.includes(":")) return Number.parseFloat(value) || 0;

    const parts = value.split(":");
    return (Number.parseInt(parts[0], 10) || 0) * 60
        + (Number.parseFloat(parts[1]) || 0);
}

function moveStart() {
    const player = document.getElementById("player");
    player.currentTime = parseTime(document.getElementById("startTime").value);
}

function moveEnd() {
    const player = document.getElementById("player");
    player.currentTime = parseTime(document.getElementById("endTime").value);
}

function captureStart() {
    const player = document.getElementById("player");
    document.getElementById("startTime").value = formatTime(player.currentTime);
}

function captureEnd() {
    const player = document.getElementById("player");
    document.getElementById("endTime").value = formatTime(player.currentTime);
}

async function createClip() {
    const fileName = ClipBrowser.getSelectedFilePath();
    const startTime = parseTime(document.getElementById("startTime").value);
    const endTime = parseTime(document.getElementById("endTime").value);
    const clipName = document.getElementById("clipName").value.trim();

    const response = await fetch("/music/clips/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fileName, startTime, endTime, clipName }),
    });

    const result = await response.json();
    alert("생성 완료 : " + result.fileName);
}

function changePlaybackRate() {
    const player = document.getElementById("player");
    player.playbackRate = parseFloat(document.getElementById("playbackRate").value);
}

async function createPitchVersion() {
    const fileName = ClipBrowser.getSelectedFilePath();
    const semitones = parseInt(document.getElementById("pitch").value, 10);

    const response = await fetch("/music/clips/pitch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fileName, semitones }),
    });

    const result = await response.json();
    alert("생성 완료 : " + result.fileName);
}

document.addEventListener("DOMContentLoaded", ClipBrowser.init);
