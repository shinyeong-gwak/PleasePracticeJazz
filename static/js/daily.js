const DAILY_TOPICS = ["박자", "테크닉", "톤", "보이싱", "스케일", "카피"];

const DAILY_STATE = {
    weekLabel: "",
    homework: [],
    practice: [],
    ensemble: [],
    tuneSuggestions: [],
    editingPracticeId: null,
    draggedHomeworkId: null,
    activeMobileTarget: null,
    metronome: {
        audioContext: null,
        timerId: null,
        feel: null,
    },
    mobileToolsCollapsed: false,
};

function formatDailyDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = `${today.getMonth() + 1}`.padStart(2, "0");
    const date = `${today.getDate()}`.padStart(2, "0");
    return `${year}.${month}.${date}`;
}

function updateStateFromReport(report) {
    DAILY_STATE.weekLabel = report.weekLabel || "";
    DAILY_STATE.homework = report.homework || [];
    DAILY_STATE.practice = report.practice || [];
    DAILY_STATE.ensemble = report.ensemble || [];
}

function loadInitialReport() {
    const node = document.getElementById("daily-report-data");

    if (!node) {
        return;
    }

    try {
        updateStateFromReport(JSON.parse(node.textContent));
    } catch (error) {
        console.error("daily report parse error", error);
    }
}

function loadInitialTuneSuggestions() {
    const node = document.getElementById("daily-tune-suggestions-data");

    if (!node) {
        return;
    }

    try {
        DAILY_STATE.tuneSuggestions = JSON.parse(node.textContent) || [];
    } catch (error) {
        console.error("daily tune suggestions parse error", error);
        DAILY_STATE.tuneSuggestions = [];
    }
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(`request failed: ${response.status}`);
    }

    return response.json();
}

function renderTuneSuggestions() {
    const dataList = document.getElementById("dailyTuneSuggestions");

    if (!dataList) {
        return;
    }

    const titles = new Set(
        DAILY_STATE.tuneSuggestions
            .concat(DAILY_STATE.practice.map((item) => item.title || ""))
            .concat(DAILY_STATE.ensemble.map((item) => item.title || ""))
            .map((title) => `${title}`.trim())
            .filter(Boolean)
    );

    dataList.innerHTML = "";

    Array.from(titles)
        .sort((left, right) => left.localeCompare(right, "ko"))
        .forEach((title) => {
            const option = document.createElement("option");
            option.value = title;
            dataList.appendChild(option);
        });
}

function bindTopicButtons() {
    const topicButtons = document.querySelectorAll("#practiceTopicChips .practice-topic-chip");

    topicButtons.forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.toggle("is-selected");
        });
    });
}

function bindStatusButtons() {
    const buttons = document.querySelectorAll(".practice-status-chip");
    const input = document.getElementById("practiceStatusInput");

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            buttons.forEach((chip) => chip.classList.remove("is-selected"));
            button.classList.add("is-selected");
            input.value = button.dataset.status || "normal";
        });
    });
}

function getStatusLabel(status) {
    if (status === "bad") {
        return "별로였음";
    }

    if (status === "good") {
        return "잘 됐음";
    }

    return "무난했음";
}

function getMetronomeLabel(enabled) {
    return enabled ? "메트로놈 O" : "메트로놈 X";
}

function buildPracticeMeta(item) {
    const parts = [];

    if (item.bpm) {
        parts.push(`${item.bpm} BPM`);
    }

    if (item.book) {
        parts.push(item.book);
    }

    if (item.page) {
        parts.push(`p.${item.page}`);
    }

    return parts.join(" · ");
}

function getMobileTargetTitle(target) {
    return target?.title?.trim() || "선택된 노트 없음";
}

function getMobileTargetBpm(target) {
    return target?.bpm?.trim() || "";
}

function updateMobileToolState() {
    const titleNode = document.getElementById("mobileToolTitle");
    const subtitleNode = document.getElementById("mobileToolSubtitle");
    const irealValue = document.getElementById("mobileIrealValue");
    const metro2Value = document.getElementById("mobileMetro2Value");
    const metro4Value = document.getElementById("mobileMetro4Value");
    const goodnotesValue = document.getElementById("mobileGoodnotesValue");
    const spotifyValue = document.getElementById("mobileSpotifyValue");
    const target = DAILY_STATE.activeMobileTarget;
    const bpm = getMobileTargetBpm(target);
    const title = getMobileTargetTitle(target);
    const noteKind = target?.kind === "ensemble" ? "합주" : "연습";
    const pageLabel = target?.book
        ? `${target.book}${target?.page ? ` · p.${target.page}` : ""}`
        : target?.page
            ? `p.${target.page}`
            : "";
    const spotifyLabel = target?.spotifyUrl ? "연결됨" : "링크";

    if (!titleNode) {
        return;
    }

    titleNode.textContent = title;
    subtitleNode.textContent = bpm
        ? `${bpm} BPM · ${noteKind} 노트 기준${pageLabel ? ` · ${pageLabel}` : ""}`
        : `${noteKind} 노트 기준${pageLabel ? ` · ${pageLabel}` : ""}`;
    irealValue.textContent = title === "선택된 노트 없음" ? "제목" : title;
    goodnotesValue.textContent = pageLabel || "악보";
    metro2Value.textContent = bpm ? `${bpm} → 2필` : "BPM";
    metro4Value.textContent = bpm ? `${bpm} → 4필` : "BPM";
    spotifyValue.textContent = spotifyLabel;
    syncMetronomeButtons();
}

function setActiveMobileTarget(target) {
    DAILY_STATE.activeMobileTarget = target;
    updateMobileToolState();
}

function getPracticeFormTarget() {
    return {
        kind: "practice",
        title: document.getElementById("practiceTuneInput").value.trim(),
        bpm: document.getElementById("practiceBpmInput").value.trim(),
        book: document.getElementById("practiceBookInput").value.trim(),
        page: document.getElementById("practicePageInput").value.trim(),
        spotifyUrl: document.getElementById("practiceSpotifyInput").value.trim(),
    };
}

function getEnsembleFormTarget() {
    return {
        kind: "ensemble",
        title: document.getElementById("ensembleTitleInput").value.trim(),
        bpm: document.getElementById("ensembleBpmInput").value.trim(),
        book: document.getElementById("ensembleBookInput").value.trim(),
        page: document.getElementById("ensemblePageInput").value.trim(),
        spotifyUrl: document.getElementById("ensembleSpotifyInput").value.trim(),
    };
}

function bindMobileTargetInputs() {
    [
        "practiceTuneInput",
        "practiceBpmInput",
        "practiceBookInput",
        "practicePageInput",
        "practiceSpotifyInput",
        "ensembleTitleInput",
        "ensembleBpmInput",
        "ensembleBookInput",
        "ensemblePageInput",
        "ensembleSpotifyInput",
    ].forEach((id) => {
        const element = document.getElementById(id);

        if (!element) {
            return;
        }

        element.addEventListener("focus", () => {
            setActiveMobileTarget(
                id.startsWith("ensemble")
                    ? getEnsembleFormTarget()
                    : getPracticeFormTarget()
            );
        });

        element.addEventListener("input", () => {
            setActiveMobileTarget(
                id.startsWith("ensemble")
                    ? getEnsembleFormTarget()
                    : getPracticeFormTarget()
            );
        });
    });
}

function stopMetronome() {
    if (DAILY_STATE.metronome.timerId) {
        clearInterval(DAILY_STATE.metronome.timerId);
    }

    DAILY_STATE.metronome.timerId = null;
    DAILY_STATE.metronome.feel = null;
    syncMetronomeButtons();
}

function ensureAudioContext() {
    if (!DAILY_STATE.metronome.audioContext) {
        DAILY_STATE.metronome.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    return DAILY_STATE.metronome.audioContext;
}

function playClick(accent = false) {
    const context = ensureAudioContext();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const now = context.currentTime;

    oscillator.type = "square";
    oscillator.frequency.value = accent ? 1320 : 880;
    gain.gain.setValueAtTime(accent ? 0.18 : 0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.08);

    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(now);
    oscillator.stop(now + 0.08);
}

function startMetronome(feelDivider) {
    const target = DAILY_STATE.activeMobileTarget;
    const bpm = parseInt(getMobileTargetBpm(target), 10);

    if (!bpm) {
        alert("현재 선택된 노트에 BPM이 없습니다.");
        return;
    }

    if (DAILY_STATE.metronome.feel === feelDivider) {
        stopMetronome();
        return;
    }

    stopMetronome();
    ensureAudioContext().resume();

    const intervalMs = Math.max(120, (60000 / bpm) * feelDivider);
    let count = 0;

    playClick(true);
    DAILY_STATE.metronome.feel = feelDivider;
    DAILY_STATE.metronome.timerId = window.setInterval(() => {
        playClick(count % 2 === 0);
        count += 1;
    }, intervalMs);
    syncMetronomeButtons();
}

function syncMetronomeButtons() {
    const metro2Button = document.getElementById("mobileMetro2Button");
    const metro4Button = document.getElementById("mobileMetro4Button");

    if (!metro2Button || !metro4Button) {
        return;
    }

    metro2Button.classList.toggle("is-active", DAILY_STATE.metronome.feel === 2);
    metro4Button.classList.toggle("is-active", DAILY_STATE.metronome.feel === 1);
}

function bindMobileToolButtons() {
    const tools = document.getElementById("practiceMobileTools");
    const irealButton = document.getElementById("mobileIrealButton");
    const metro2Button = document.getElementById("mobileMetro2Button");
    const metro4Button = document.getElementById("mobileMetro4Button");
    const goodnotesButton = document.getElementById("mobileGoodnotesButton");
    const spotifyButton = document.getElementById("mobileSpotifyButton");
    const toggleButton = document.getElementById("mobileToolsToggleButton");

    if (!irealButton) {
        return;
    }

    if (toggleButton && tools) {
        toggleButton.addEventListener("click", () => {
            DAILY_STATE.mobileToolsCollapsed = !DAILY_STATE.mobileToolsCollapsed;
            tools.classList.toggle("is-collapsed", DAILY_STATE.mobileToolsCollapsed);
            toggleButton.textContent = DAILY_STATE.mobileToolsCollapsed ? "펼치기" : "접기";
            toggleButton.setAttribute("aria-expanded", DAILY_STATE.mobileToolsCollapsed ? "false" : "true");
        });
    }

    irealButton.addEventListener("click", () => {
        const title = encodeURIComponent(getMobileTargetTitle(DAILY_STATE.activeMobileTarget));

        if (!title || title === encodeURIComponent("선택된 노트 없음")) {
            return;
        }

        window.location.href = `irealb://search?${title}`;
    });

    metro2Button.addEventListener("click", () => startMetronome(2));
    metro4Button.addEventListener("click", () => startMetronome(1));

    goodnotesButton.addEventListener("click", () => {
        alert("Goodnotes 버튼은 준비만 해두었어요. 연결 스키마를 정하면 바로 이어붙일 수 있습니다.");
    });

    spotifyButton.addEventListener("click", () => {
        const url = DAILY_STATE.activeMobileTarget?.spotifyUrl;

        if (!url) {
            alert("현재 선택된 노트에 Spotify 링크가 없습니다.");
            return;
        }

        window.location.href = url;
    });
}

function getSelectedPracticeTopics() {
    return Array.from(
        document.querySelectorAll("#practiceTopicChips .practice-topic-chip.is-selected")
    ).map((button) => button.dataset.topic);
}

function setSelectedPracticeTopics(topics) {
    const topicSet = new Set(topics || []);

    document.querySelectorAll("#practiceTopicChips .practice-topic-chip").forEach((button) => {
        button.classList.toggle("is-selected", topicSet.has(button.dataset.topic));
    });
}

function setPracticeStatus(status) {
    const value = status || "normal";
    document.getElementById("practiceStatusInput").value = value;

    document.querySelectorAll(".practice-status-chip").forEach((button) => {
        button.classList.toggle("is-selected", button.dataset.status === value);
    });
}

function resetPracticeForm() {
    DAILY_STATE.editingPracticeId = null;
    document.getElementById("practiceBpmInput").value = "";
    document.getElementById("practiceTuneInput").value = "";
    document.getElementById("practiceBookInput").value = "";
    document.getElementById("practicePageInput").value = "";
    document.getElementById("practiceMemoInput").value = "";
    document.getElementById("practiceSpotifyInput").value = "";
    setSelectedPracticeTopics([]);
    setPracticeStatus("normal");
    document.getElementById("addPracticeCardButton").textContent = "+ 카드 추가";
    document.getElementById("cancelPracticeEditButton").classList.add("hidden");
    setActiveMobileTarget(getPracticeFormTarget());
}

function fillPracticeForm(item) {
    DAILY_STATE.editingPracticeId = item.id;
    document.getElementById("practiceBpmInput").value = item.bpm || "";
    document.getElementById("practiceTuneInput").value = item.title || "";
    document.getElementById("practiceBookInput").value = item.book || "";
    document.getElementById("practicePageInput").value = item.page || "";
    document.getElementById("practiceMemoInput").value = item.memo || "";
    document.getElementById("practiceSpotifyInput").value = item.spotifyUrl || "";
    setSelectedPracticeTopics(item.topics || []);
    setPracticeStatus(item.status || "normal");
    document.getElementById("addPracticeCardButton").textContent = "수정 저장";
    document.getElementById("cancelPracticeEditButton").classList.remove("hidden");
    document.getElementById("practiceEditorCard").scrollIntoView({
        behavior: "smooth",
        block: "start",
    });
    setActiveMobileTarget({
        kind: "practice",
        title: item.title || "",
        bpm: item.bpm || "",
        book: item.book || "",
        page: item.page || "",
        spotifyUrl: item.spotifyUrl || "",
    });
}

function collectPracticePayload() {
    return {
        title: document.getElementById("practiceTuneInput").value.trim(),
        bpm: document.getElementById("practiceBpmInput").value.trim(),
        book: document.getElementById("practiceBookInput").value.trim(),
        page: document.getElementById("practicePageInput").value.trim(),
        spotifyUrl: document.getElementById("practiceSpotifyInput").value.trim(),
        topics: getSelectedPracticeTopics(),
        status: document.getElementById("practiceStatusInput").value.trim() || "normal",
        memo: document.getElementById("practiceMemoInput").value.trim(),
    };
}

function collectHomeworkPayload() {
    return {
        title: document.getElementById("practiceHomeworkTitleInput").value.trim(),
        memo: document.getElementById("practiceHomeworkMemoInput").value.trim(),
    };
}

function resetHomeworkEditor() {
    document.getElementById("practiceHomeworkTitleInput").value = "";
    document.getElementById("practiceHomeworkMemoInput").value = "";
}

function collectEnsemblePayload() {
    return {
        title: document.getElementById("ensembleTitleInput").value.trim(),
        bpm: document.getElementById("ensembleBpmInput").value.trim(),
        book: document.getElementById("ensembleBookInput").value.trim(),
        page: document.getElementById("ensemblePageInput").value.trim(),
        spotifyUrl: document.getElementById("ensembleSpotifyInput").value.trim(),
        topics: document.getElementById("ensembleTopicsInput").value.trim(),
        status: document.getElementById("ensembleStatusInput").value.trim() || "normal",
        memo: document.getElementById("ensembleMemoInput").value.trim(),
    };
}

function resetEnsembleEditor() {
    document.getElementById("ensembleTitleInput").value = "";
    document.getElementById("ensembleBpmInput").value = "";
    document.getElementById("ensembleBookInput").value = "";
    document.getElementById("ensemblePageInput").value = "";
    document.getElementById("ensembleSpotifyInput").value = "";
    document.getElementById("ensembleTopicsInput").value = "";
    document.getElementById("ensembleStatusInput").value = "normal";
    document.getElementById("ensembleMemoInput").value = "";
}

function bindHomeworkBoardAutoScroll() {
    const board = document.getElementById("practiceHomeworkBoard");

    if (!board) {
        return;
    }

    board.addEventListener("dragover", (event) => {
        event.preventDefault();

        const rect = board.getBoundingClientRect();
        const edge = 72;
        const step = 18;

        if (event.clientX < rect.left + edge) {
            board.scrollLeft -= step;
        } else if (event.clientX > rect.right - edge) {
            board.scrollLeft += step;
        }
    });

    board.addEventListener("drop", () => {
        DAILY_STATE.draggedHomeworkId = null;
    });
}

function renderHomeworkBoard() {
    const board = document.getElementById("practiceHomeworkBoard");
    const template = document.getElementById("practiceHomeworkTemplate");

    board.innerHTML = "";

    DAILY_STATE.homework.forEach((item) => {
        const fragment = template.content.cloneNode(true);
        const note = fragment.querySelector(".practice-homework-note");
        const title = fragment.querySelector(".practice-homework-note-title");
        const body = fragment.querySelector(".practice-homework-note-body");
        const remove = fragment.querySelector(".practice-homework-remove-button");

        note.dataset.homeworkId = item.id;
        title.textContent = item.title;
        body.textContent = item.memo;

        title.addEventListener("blur", async () => {
            const report = await requestJson(`/music/daily/homework/${item.id}`, {
                method: "PUT",
                body: JSON.stringify({
                    title: title.textContent.trim(),
                    memo: body.textContent.trim(),
                }),
            });
            updateStateFromReport(report);
            renderAll();
        });

        body.addEventListener("blur", async () => {
            const report = await requestJson(`/music/daily/homework/${item.id}`, {
                method: "PUT",
                body: JSON.stringify({
                    title: title.textContent.trim(),
                    memo: body.textContent.trim(),
                }),
            });
            updateStateFromReport(report);
            renderAll();
        });

        remove.addEventListener("click", async () => {
            const report = await requestJson(`/music/daily/homework/${item.id}`, {
                method: "DELETE",
            });
            updateStateFromReport(report);
            renderAll();
        });

        note.addEventListener("dragstart", () => {
            DAILY_STATE.draggedHomeworkId = item.id;
        });

        note.addEventListener("dragend", () => {
            DAILY_STATE.draggedHomeworkId = null;
            note.classList.remove("is-drop-target");
        });

        note.addEventListener("dragover", (event) => {
            event.preventDefault();
            note.classList.add("is-drop-target");
        });

        note.addEventListener("dragleave", () => {
            note.classList.remove("is-drop-target");
        });

        note.addEventListener("drop", async (event) => {
            event.preventDefault();
            note.classList.remove("is-drop-target");

            if (!DAILY_STATE.draggedHomeworkId || DAILY_STATE.draggedHomeworkId === item.id) {
                return;
            }

            const report = await requestJson("/music/daily/homework/merge", {
                method: "POST",
                body: JSON.stringify({
                    sourceId: DAILY_STATE.draggedHomeworkId,
                    targetId: item.id,
                }),
            });

            DAILY_STATE.draggedHomeworkId = null;
            updateStateFromReport(report);
            renderAll();
        });

        board.appendChild(fragment);
    });
}

function createEnsembleCardNode(item, template) {
    const fragment = template.content.cloneNode(true);
    const card = fragment.querySelector(".practice-ensemble-note");
    const titleInput = fragment.querySelector(".practice-inline-title");
    const bpmInput = fragment.querySelector(".practice-inline-bpm");
    const bookInput = fragment.querySelector(".practice-inline-book");
    const pageInput = fragment.querySelector(".practice-inline-page");
    const statusInput = fragment.querySelector(".practice-inline-status");
    const spotifyInput = fragment.querySelector(".practice-inline-spotify");
    const topicsInput = fragment.querySelector(".practice-inline-topics");
    const memoInput = fragment.querySelector(".practice-inline-memo");
    const removeButton = fragment.querySelector(".practice-homework-remove-button");

    card.dataset.ensembleId = item.id;
    card.classList.toggle("practice-ensemble-note-bad", item.status === "bad");
    card.classList.toggle("practice-ensemble-note-good", item.status === "good");
    titleInput.value = item.title || "";
    bpmInput.value = item.bpm || "";
    bookInput.value = item.book || "";
    pageInput.value = item.page || "";
    statusInput.value = item.status || "normal";
    spotifyInput.value = item.spotifyUrl || "";
    topicsInput.value = (item.topics || []).join(", ");
    memoInput.value = item.memo || "";

    async function saveInline() {
        const report = await requestJson(`/music/daily/ensemble/${item.id}`, {
            method: "PUT",
            body: JSON.stringify({
                title: titleInput.value.trim(),
                bpm: bpmInput.value.trim(),
                book: bookInput.value.trim(),
                page: pageInput.value.trim(),
                spotifyUrl: spotifyInput.value.trim(),
                status: statusInput.value.trim(),
                topics: topicsInput.value.trim(),
                memo: memoInput.value.trim(),
            }),
        });
        updateStateFromReport(report);
        renderAll();
    }

    [titleInput, bpmInput, bookInput, pageInput, statusInput, spotifyInput, topicsInput, memoInput]
        .forEach((field) => {
            const eventName = field.tagName === "SELECT" ? "change" : "blur";
            field.addEventListener(eventName, saveInline);
            field.addEventListener("focus", () => {
                setActiveMobileTarget({
                    kind: "ensemble",
                    title: titleInput.value.trim(),
                    bpm: bpmInput.value.trim(),
                    book: bookInput.value.trim(),
                    page: pageInput.value.trim(),
                    spotifyUrl: spotifyInput.value.trim(),
                });
            });
            field.addEventListener("input", () => {
                setActiveMobileTarget({
                    kind: "ensemble",
                    title: titleInput.value.trim(),
                    bpm: bpmInput.value.trim(),
                    book: bookInput.value.trim(),
                    page: pageInput.value.trim(),
                    spotifyUrl: spotifyInput.value.trim(),
                });
            });
        });

    removeButton.addEventListener("click", async () => {
        const report = await requestJson(`/music/daily/ensemble/${item.id}`, {
            method: "DELETE",
        });
        updateStateFromReport(report);
        renderAll();
    });

    return fragment;
}

function renderEnsembleBoard() {
    const board = document.getElementById("ensembleBoard");
    const template = document.getElementById("ensembleCardTemplate");

    board.innerHTML = "";

    DAILY_STATE.ensemble.forEach((item) => {
        board.appendChild(createEnsembleCardNode(item, template));
    });
}

function renderPracticeCards() {
    const cards = document.getElementById("practiceCards");
    const template = document.getElementById("practiceCardTemplate");

    cards.innerHTML = "";

    DAILY_STATE.practice.forEach((item) => {
        const fragment = template.content.cloneNode(true);
        const card = fragment.querySelector(".practice-summary-card");
        const removeButton = fragment.querySelector(".practice-remove-button");
        const hasMetronome = !!item.metronome;

        card.dataset.practiceId = item.id;
        card.classList.toggle("practice-summary-card-bad", item.status === "bad" || !hasMetronome);
        card.classList.toggle("practice-summary-card-good", item.status === "good");
        fragment.querySelector(".practice-summary-title").textContent = item.title || "이름 없는 연습";
        fragment.querySelector(".practice-summary-topline").textContent = item.page
            ? `${item.book || "악보집 미지정"} · p.${item.page}`
            : item.book || "악보집 미지정";
        fragment.querySelector(".practice-summary-status").textContent = getStatusLabel(item.status);
        fragment.querySelector(".practice-summary-status").className = `practice-summary-status practice-summary-status-${item.status || "normal"}`;
        fragment.querySelector(".practice-summary-bpm").textContent = item.bpm ? `${item.bpm} BPM` : "BPM 없음";
        fragment.querySelector(".practice-summary-book").textContent = (item.topics || []).length
            ? item.topics.map((topic) => `#${topic}`).join(" ")
            : "주제 미지정";
        fragment.querySelector(".practice-summary-metro").className = `practice-summary-metro ${hasMetronome ? "hidden" : ""}`;
        fragment.querySelector(".practice-summary-topics").textContent = item.memo || "한줄 평 없음";
        fragment.querySelector(".practice-summary-memo").textContent = buildPracticeMeta(item) || "악보 정보 없음";

        card.addEventListener("click", (event) => {
            if (event.target.closest(".practice-remove-button")) {
                return;
            }

            setActiveMobileTarget({
                kind: "practice",
                title: item.title || "",
                bpm: item.bpm || "",
                book: item.book || "",
                page: item.page || "",
                spotifyUrl: item.spotifyUrl || "",
            });
            fillPracticeForm(item);
        });

        removeButton.addEventListener("click", async (event) => {
            event.stopPropagation();
            const report = await requestJson(`/music/daily/practice/${item.id}`, {
                method: "DELETE",
            });
            updateStateFromReport(report);

            if (DAILY_STATE.editingPracticeId === item.id) {
                resetPracticeForm();
            }

            renderAll();
        });

        cards.appendChild(fragment);
    });
}

function renderAll() {
    renderTuneSuggestions();
    renderHomeworkBoard();
    renderEnsembleBoard();
    renderPracticeCards();
}

async function addHomework() {
    const payload = collectHomeworkPayload();

    if (!payload.title && !payload.memo) {
        return;
    }

    const report = await requestJson("/music/daily/homework", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    updateStateFromReport(report);
    resetHomeworkEditor();
    renderAll();
}

async function savePractice() {
    const payload = collectPracticePayload();

    const report = await requestJson(
        DAILY_STATE.editingPracticeId
            ? `/music/daily/practice/${DAILY_STATE.editingPracticeId}`
            : "/music/daily/practice",
        {
            method: DAILY_STATE.editingPracticeId ? "PUT" : "POST",
            body: JSON.stringify(payload),
        }
    );

    updateStateFromReport(report);
    resetPracticeForm();
    renderAll();
}

async function addEnsemble() {
    const payload = collectEnsemblePayload();

    if (!payload.title && !payload.memo) {
        return;
    }

    const report = await requestJson("/music/daily/ensemble", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    updateStateFromReport(report);
    resetEnsembleEditor();
    renderAll();
}

function initPracticeDailyPage() {
    if (!document.getElementById("practiceEditorCard")) {
        return;
    }

    loadInitialReport();
    loadInitialTuneSuggestions();
    bindTopicButtons();
    bindStatusButtons();
    bindHomeworkBoardAutoScroll();

    document.getElementById("practiceDailyDate").textContent = formatDailyDate();
    document.getElementById("addHomeworkButton").addEventListener("click", addHomework);
    document.getElementById("addEnsembleButton").addEventListener("click", addEnsemble);
    document.getElementById("addPracticeCardButton").addEventListener("click", savePractice);
    document.getElementById("cancelPracticeEditButton").addEventListener("click", resetPracticeForm);
    bindMobileTargetInputs();
    bindMobileToolButtons();
    setActiveMobileTarget(getPracticeFormTarget());

    renderAll();
}

document.addEventListener("DOMContentLoaded", initPracticeDailyPage);
window.addEventListener("pagehide", stopMetronome);
document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        stopMetronome();
    }
});
