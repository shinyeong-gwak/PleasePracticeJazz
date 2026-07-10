const ClipBrowser = (() => {
    let payload = { library: null, pool: [] };
    let selectedFilePath = "";
    let selectedFolderId = "";
    let selectedTrackId = "";
    let selectedTrackFolderId = "";
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

            if (sortMode === "name-desc") {
                return String(b.name || "").localeCompare(String(a.name || ""), "ko");
            }

            return String(a.name || "").localeCompare(String(b.name || ""), "ko");
        });
        return sorted;
    }

    function poolTracks() {
        return payload.pool || [];
    }

    function findTrackNode(node, trackId) {
        if (!node) return null;
        if (node.type === "file" && node.id === trackId) return node;
        for (const child of node.children || []) {
            const found = findTrackNode(child, trackId);
            if (found) return found;
        }
        return null;
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
        if (!label) return;

        label.textContent = selectedFilePath || "?좏깮???뚯썝???놁뼱??";
    }

    function selectFile(path, trackId = "", folderId = "") {
        selectedFilePath = path;
        selectedTrackId = trackId;
        selectedTrackFolderId = folderId || "";

        const select = fileSelect();
        if (select) select.value = path;

        syncSelectedLabel();
        renderTree();
    }

    function setSelectedTrackFromNode(item) {
        selectFile(item.path, item.id, item.folderId || "");
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

    function runTrackMutation(action) {
        return action()
            .then((nextPayload) => refreshTree(nextPayload))
            .catch((error) => showTreeError(error));
    }

    function makeTrackActionButton(label, title, handler) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "tree-action-button";
        button.textContent = label;
        button.title = title;
        button.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            handler();
        });
        return button;
    }

    function makeLibraryFileRow(item, depth) {
        const row = document.createElement("div");
        row.className = "audio-tree-file-row";
        row.style.setProperty("--depth", depth);

        if (item.id === selectedTrackId || item.path === selectedFilePath) {
            row.classList.add("is-selected");
        }

        const main = document.createElement("button");
        main.type = "button";
        main.className = "audio-tree-row audio-tree-file-main";

        const icon = document.createElement("span");
        icon.className = "audio-tree-icon";
        icon.textContent = "♪";

        const name = document.createElement("span");
        name.className = "audio-tree-name";
        name.textContent = item.name;

        main.append(icon, name);
        main.addEventListener("click", () => {
            setSelectedTrackFromNode(item);
            loadAudio();
        });

        const actions = document.createElement("div");
        actions.className = "audio-tree-file-actions";

        actions.append(
            makeTrackActionButton("▴", "위로", () => runTrackMutation(() =>
                mutateLibraryItem("/music/clips/library-items/reorder", {
                    trackId: item.trackId || item.id,
                    direction: "up",
                })
            )),
            makeTrackActionButton("▾", "아래로", () => runTrackMutation(() =>
                mutateLibraryItem("/music/clips/library-items/reorder", {
                    trackId: item.trackId || item.id,
                    direction: "down",
                })
            )),
            makeTrackActionButton("↩", "루트로", () => runTrackMutation(() =>
                mutateLibraryItem("/music/clips/library-items/move", {
                    trackId: item.trackId || item.id,
                    folderId: "",
                })
            ))
        );

        row.append(main, actions);
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
            throw new Error(data.message || "?붿껌??泥섎━?섏? 紐삵뻽?댁슂.");
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

    function renderTree() {
        const container = node("[data-audio-tree]");
        if (!container) return;

        container.innerHTML = "";

        if (!payload.library && !poolTracks().length) {
            container.innerHTML = '<div class="audio-tree-empty">No tracks yet.</div>';
            return;
        }

        container.appendChild(sectionTitle("Library"));
        if (payload.library?.children?.length) {
            renderLibraryNode(payload.library, 0, container);
        } else {
            const empty = document.createElement("div");
            empty.className = "audio-tree-empty";
            empty.textContent = "No library items yet.";
            container.appendChild(empty);
        }

        container.appendChild(sectionTitle("Public Pool"));
        if (poolTracks().length) {
            poolTracks().forEach((track) => {
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
                addButton.title = "Add to selected folder";
                addButton.addEventListener("click", async () => {
                    await addTrackToLibrary(track.id);
                });

                row.append(selectButton, addButton);
                container.appendChild(row);
            });
        } else {
            const empty = document.createElement("div");
            empty.className = "audio-tree-empty";
            empty.textContent = "No public tracks.";
            container.appendChild(empty);
        }
    }

    function showTreeError(error) {
        const container = node("[data-audio-tree]");
        if (container) {
            container.innerHTML = `<div class="audio-tree-empty">${error.message || "?뚯썝??遺덈윭?ㅼ? 紐삵뻽?댁슂."}</div>`;
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

    async function mutateLibraryItem(url, body) {
        const response = await fetch(url, {
            method: "PUT",
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
                if (status) status.textContent = "?곸슜?먯뼱??";
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
                if (status) status.textContent = "??젣???대뜑瑜??좏깮??二쇱꽭??";
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
    alert("?앹꽦 ?꾨즺 : " + result.fileName);
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
    alert("?앹꽦 ?꾨즺 : " + result.fileName);
}

document.addEventListener("DOMContentLoaded", ClipBrowser.init);
