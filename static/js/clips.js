const ClipBrowser = (() => {
    let payload = { library: null, pool: [] };
    let selectedFilePath = "";
    let selectedFolderId = "";
    let sortMode = "name-asc";
    const collapsedFolders = new Set();

    function node(selector) {
        return document.querySelector(selector);
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
            return String(a.name || "").localeCompare(String(b.name || ""), "ko") * direction;
        });
        return sorted;
    }

    function poolTracks() {
        return payload.pool || [];
    }

    function syncSelectOptions() {
        const select = fileSelect();
        if (!select) return;

        select.innerHTML = "";
        poolTracks().forEach((track) => {
            const option = document.createElement("option");
            option.value = track.filePath;
            option.textContent = track.displayName || track.fileName;
            select.appendChild(option);
        });

        if (!selectedFilePath && poolTracks().length) {
            selectedFilePath = poolTracks()[0].filePath;
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

    function selectFile(path) {
        selectedFilePath = path;
        const select = fileSelect();
        if (select) select.value = path;
        syncSelectedLabel();
        renderTree();
    }

    function makeFolderRow(item, depth) {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "audio-tree-row audio-tree-folder";
        row.style.setProperty("--depth", depth);
        if (item.id === selectedFolderId) {
            row.classList.add("is-folder-selected");
        }

        const icon = document.createElement("span");
        icon.className = "audio-tree-icon";
        icon.textContent = collapsedFolders.has(item.id) ? "▸" : "▾";

        const name = document.createElement("span");
        name.className = "audio-tree-name";
        name.textContent = item.name;

        row.append(icon, name);
        row.addEventListener("click", () => {
            selectedFolderId = item.id || "";
            if (collapsedFolders.has(item.id)) {
                collapsedFolders.delete(item.id);
            } else {
                collapsedFolders.add(item.id);
            }
            renderTree();
        });
        return row;
    }

    function makeLibraryFileRow(item, depth) {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "audio-tree-row audio-tree-file";
        row.style.setProperty("--depth", depth);
        if (item.path === selectedFilePath) {
            row.classList.add("is-selected");
        }

        const icon = document.createElement("span");
        icon.className = "audio-tree-icon";
        icon.textContent = "♪";

        const name = document.createElement("span");
        name.className = "audio-tree-name";
        name.textContent = item.name;

        row.append(icon, name);
        row.addEventListener("click", () => {
            selectFile(item.path);
            loadAudio();
        });
        return row;
    }

    function renderLibraryNode(item, depth, container) {
        if (item.type === "folder") {
            if (item.id) {
                container.appendChild(makeFolderRow(item, depth));
            }
            if (!collapsedFolders.has(item.id)) {
                normalizeChildren(item.children).forEach((child) => {
                    renderLibraryNode(child, item.id ? depth + 1 : depth, container);
                });
            }
            return;
        }
        container.appendChild(makeLibraryFileRow(item, depth));
    }

    async function readJsonResponse(response) {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.message || "요청을 처리하지 못했어요.");
        }
        return data;
    }

    async function refreshTree(nextPayload = null) {
        payload = nextPayload || await readJsonResponse(await fetch("/music/clips/tree"));
        syncSelectOptions();
        renderTree();
    }

    function sectionTitle(text) {
        const title = document.createElement("div");
        title.className = "audio-tree-section-title";
        title.textContent = text;
        return title;
    }

    function makePoolRow(track) {
        const row = document.createElement("div");
        row.className = "audio-pool-row";
        if (track.filePath === selectedFilePath) {
            row.classList.add("is-selected");
        }

        const selectButton = document.createElement("button");
        selectButton.type = "button";
        selectButton.className = "audio-pool-select";
        selectButton.textContent = track.displayName || track.fileName;
        selectButton.addEventListener("click", () => {
            selectFile(track.filePath);
            loadAudio();
        });

        const addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "audio-pool-add";
        addButton.textContent = "+";
        addButton.title = "선택한 폴더에 추가";
        addButton.addEventListener("click", async () => {
            await addTrackToLibrary(track.id);
        });

        row.append(selectButton, addButton);
        return row;
    }

    function renderTree() {
        const container = node("[data-audio-tree]");
        if (!container) return;

        container.innerHTML = "";
        if (!payload.library && !poolTracks().length) {
            container.innerHTML = '<div class="audio-tree-empty">음원 풀에 등록된 트랙이 없어요.</div>';
            return;
        }

        container.appendChild(sectionTitle("내 라이브러리"));
        if (payload.library?.children?.length) {
            renderLibraryNode(payload.library, 0, container);
        } else {
            const empty = document.createElement("div");
            empty.className = "audio-tree-empty";
            empty.textContent = "아직 내 폴더에 담은 곡이 없어요.";
            container.appendChild(empty);
        }

        container.appendChild(sectionTitle("공용 음악 풀"));
        if (poolTracks().length) {
            poolTracks().forEach((track) => container.appendChild(makePoolRow(track)));
        } else {
            const empty = document.createElement("div");
            empty.className = "audio-tree-empty";
            empty.textContent = "공용 트랙이 없어요.";
            container.appendChild(empty);
        }
    }

    function showTreeError(error) {
        const container = node("[data-audio-tree]");
        if (container) {
            container.innerHTML = `<div class="audio-tree-empty">${error.message || "음원을 불러오지 못했어요."}</div>`;
        }
    }

    async function mutateFolder(method, body) {
        const response = await fetch("/music/clips/folders", {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        return readJsonResponse(response);
    }

    async function addTrackToLibrary(trackId) {
        const response = await fetch("/music/clips/library-items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                trackId,
                folderId: selectedFolderId,
            }),
        });
        await refreshTree(await readJsonResponse(response));
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
                const nextPayload = await action();
                await refreshTree(nextPayload);
                if (status) status.textContent = "반영했어요.";
                if (nameInput) nameInput.value = "";
            } catch (error) {
                if (status) status.textContent = error.message;
            }
        };

        createButton?.addEventListener("click", () => run(() => mutateFolder("POST", {
            parentId: selectedFolderId,
            name: nameInput.value,
        })));

        renameButton?.addEventListener("click", () => run(() => mutateFolder("PUT", {
            folderId: selectedFolderId,
            name: nameInput.value,
        })));

        deleteButton?.addEventListener("click", () => {
            if (!selectedFolderId) {
                if (status) status.textContent = "삭제할 폴더를 선택해주세요.";
                return;
            }
            run(() => mutateFolder("DELETE", { folderId: selectedFolderId }));
        });
    }

    function init() {
        bindFolderMenu();
        void refreshTree().catch(showTreeError);
    }

    return {
        init,
        getSelectedFilePath: () => selectedFilePath || fileSelect()?.value || "",
    };
})();

window.ClipBrowser = ClipBrowser;

function loadAudio() {
    const fileName = ClipBrowser.getSelectedFilePath();
    const player = document.getElementById("player");

    if (!fileName || !player) return;

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
