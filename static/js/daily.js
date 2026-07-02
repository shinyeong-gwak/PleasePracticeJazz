const DAILY_TOPICS = ["Rhythm", "Solo", "Ensemble", "Voicing", "Practice", "Etude"];

const DAILY_STATE = {
    weekKey: "",
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
        masterGain: null,
        timerId: null,
        feel: null,
        pulseCount: 0,
        unlocked: false,
    },
    mobileToolsCollapsed: false,
};

function formatDailyDate() {
    return LickSettings.formatDateLabel(new Date());
}

function updateStateFromReport(report) {
    DAILY_STATE.weekKey = report.weekKey || "";
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

function getArchiveWeekStart() {
    if (!DAILY_STATE.weekKey) {
        return null;
    }

    const value = LickSettings.parseDate(DAILY_STATE.weekKey);
    return !value || Number.isNaN(value.getTime()) ? null : value;
}

function formatArchiveDayLabel(dateValue) {
    return `${dateValue.toISOString().slice(5, 7)}.${dateValue.toISOString().slice(8, 10)}`;
}

function formatLocalDateKey(dateValue) {
    return dateValue.toISOString().slice(0, 10);
}

function getArchiveWeekdays() {
    const weekStart = getArchiveWeekStart();
    const weekdays = LickSettings.getWeekdayLabels();

    if (!weekStart) {
        return [];
    }

    return weekdays.map((weekday, index) => {
        const dateValue = new Date(weekStart);
        dateValue.setUTCDate(weekStart.getUTCDate() + index);

        return {
            weekday,
            date: formatLocalDateKey(dateValue),
            label: formatArchiveDayLabel(dateValue),
            practice: [],
            ensemble: [],
            count: 0,
            missingMetronome: false,
        };
    });
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

function groupCurrentArchive() {
    const buckets = getArchiveWeekdays();
    const bucketMap = new Map(
        buckets.map((bucket) => [bucket.date, bucket])
    );

    for (const item of DAILY_STATE.practice) {
        const dayKey = LickSettings.formatDateKey(item.createdAt);
        const bucket = bucketMap.get(dayKey);

        if (!bucket) {
            continue;
        }

        bucket.practice.push(item);
        bucket.count += 1;
        bucket.missingMetronome = bucket.missingMetronome || !item.metronome;
    }

    for (const item of DAILY_STATE.ensemble) {
        const dayKey = LickSettings.formatDateKey(item.createdAt);
        const bucket = bucketMap.get(dayKey);

        if (!bucket) {
            continue;
        }

        bucket.ensemble.push(item);
        bucket.count += 1;
        bucket.missingMetronome = bucket.missingMetronome || !item.metronome;
    }

    return buckets.map((bucket) => ({
        ...bucket,
        isEmpty: bucket.count === 0,
        isBad: bucket.count === 0 || bucket.missingMetronome,
    }));
}

function buildArchiveItemMarkup(item, kind) {
    const meta = [];

    if (item.bpm) {
        meta.push(`${item.bpm} BPM`);
    }

    if (item.book) {
        meta.push(item.book);
    }

    if (item.page) {
        meta.push(`p.${item.page}`);
    }

    return `
        <article
            class="practice-report-item practice-mobile-target-card ${item.status === "bad" || !item.metronome ? "practice-report-item-bad" : item.status === "good" ? "practice-report-item-good" : ""}"
            data-target-kind="${kind}"
            data-target-title="${item.title || ""}"
            data-target-bpm="${item.bpm || ""}"
            data-target-book="${item.book || ""}"
            data-target-page="${item.page || ""}"
            data-target-spotify="${item.spotifyUrl || ""}"
            data-target-lick="${item.lickFile || ""}"
            data-target-renderer="${item.rendererFile || ""}"
            data-target-status="${item.status || "normal"}"
            data-target-memo="${item.memo || ""}"
            data-target-topics="${(item.topics || []).join(", ")}"
        >
            <div class="practice-report-item-title">${item.title || (kind === "ensemble" ? "제목 없는 합주" : "제목 없는 연습")}</div>
            <div class="practice-report-item-meta">${kind === "ensemble" ? "합주" : "연습"}${meta.length ? ` · ${meta.join(" · ")}` : ""}</div>
            <div class="practice-report-item-copy">${item.memo || "메모 없음"}</div>
        </article>
    `;
}

function buildTargetFromDataset(node) {
    if (!node) {
        return null;
    }

    return {
        kind: node.dataset.targetKind || "practice",
        title: node.dataset.targetTitle || "",
        bpm: node.dataset.targetBpm || "",
        book: node.dataset.targetBook || "",
        page: node.dataset.targetPage || "",
        spotifyUrl: node.dataset.targetSpotify || "",
        lickFile: node.dataset.targetLick || "",
        rendererFile: node.dataset.targetRenderer || "",
        status: node.dataset.targetStatus || "normal",
        memo: node.dataset.targetMemo || "",
        topics: node.dataset.targetTopics || "",
    };
}

async function duplicateArchiveTarget(target) {
    if (!target?.kind) {
        return;
    }

    const payload = {
        title: target.title || "",
        bpm: target.bpm || "",
        book: target.book || "",
        page: target.page || "",
        spotifyUrl: target.spotifyUrl || "",
        lickFile: target.lickFile || "",
        rendererFile: target.rendererFile || "",
        status: target.status || "normal",
        topics: target.topics || "",
        memo: target.memo || "",
    };
    const endpoint = target.kind === "ensemble"
        ? "/music/daily/ensemble"
        : "/music/daily/practice";
    const report = await requestJson(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
    });

    updateStateFromReport(report);
    setActiveMobileTarget(target);
    renderAll();
}

function renderCurrentArchive() {
    const homeworkList = document.getElementById("currentArchiveHomeworkList");
    const daysContainer = document.getElementById("currentArchiveDays");
    const weekLabelNode = document.getElementById("currentArchiveWeekLabel");

    if (!homeworkList || !daysContainer) {
        return;
    }

    if (weekLabelNode) {
        weekLabelNode.textContent = DAILY_STATE.weekLabel || "";
    }

    if (DAILY_STATE.homework.length === 0) {
        homeworkList.innerHTML = "<div class='practice-report-empty'>이번 주에 숙제가 없습니다.</div>";
    } else {
        homeworkList.innerHTML = DAILY_STATE.homework.map((item) => `
            <article class="practice-report-item">
                <div class="practice-report-item-title">${item.title}</div>
                <div class="practice-report-item-copy">${item.memo || "메모 없음"}</div>
            </article>
        `).join("");
    }

    const days = groupCurrentArchive();

    daysContainer.innerHTML = days.map((day) => `
        <section class="practice-report-day ${day.isBad ? "practice-report-day-bad" : ""}">
            <div class="practice-report-day-head">
                <div class="practice-report-day-title">${day.weekday}</div>
                <div class="practice-report-day-meta">${day.label}</div>
            </div>
            ${
                day.isEmpty
                    ? "<div class='practice-report-empty'>기록 없음</div>"
                    : `
                        <div class="practice-report-day-list">
                            ${day.practice.map((item) => buildArchiveItemMarkup(item, "practice")).join("")}
                            ${day.ensemble.map((item) => buildArchiveItemMarkup(item, "ensemble")).join("")}
                        </div>
                    `
            }
        </section>
    `).join("");

    daysContainer.querySelectorAll(".practice-mobile-target-card").forEach((card) => {
        card.addEventListener("click", async () => {
            const target = buildTargetFromDataset(card);

            if (target) {
                if (!confirmDelete("이 카드를 오늘 카드로 복제할까요?")) {
                    return;
                }
                await duplicateArchiveTarget(target);
            }
        });
    });
}

function confirmDelete(message) {
    return window.confirm(message);
}

function mergeHomework(sourceId, targetId) {
    return requestJson("/music/daily/homework/merge", {
        method: "POST",
        body: JSON.stringify({
            sourceId,
            targetId,
        }),
    });
}

function clearHomeworkMergeState() {
    DAILY_STATE.draggedHomeworkId = null;
    document.querySelectorAll(".practice-homework-note.is-merge-source").forEach((node) => {
        node.classList.remove("is-merge-source");
    });
}

function bindTapOutsideBlur() {
    document.addEventListener("pointerdown", (event) => {
        const activeElement = document.activeElement;
        const target = event.target;

        if (!activeElement || !(activeElement instanceof HTMLElement)) {
            return;
        }

        if (target instanceof HTMLElement) {
            if (target.closest("input, textarea, select, [contenteditable='true']")) {
                return;
            }
        }

        if (activeElement.matches("input, textarea, select")) {
            activeElement.blur();
            return;
        }

        if (activeElement.isContentEditable) {
            activeElement.blur();
        }
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
    return enabled ? "硫뷀듃濡쒕냸 O" : "硫뷀듃濡쒕냸 X";
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

    return parts.join(" 쨌 ");
}

function getMobileTargetTitle(target) {
    return target?.title?.trim() || "?좏깮???명듃 ?놁쓬";
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
    const realbookValue = document.getElementById("mobileRealbookValue");
    const spotifyValue = document.getElementById("mobileSpotifyValue");
    const lickValue = document.getElementById("mobileLickValue");
    const target = DAILY_STATE.activeMobileTarget;
    const bpm = getMobileTargetBpm(target);
    const title = getMobileTargetTitle(target);
    const noteKind = target?.kind === "ensemble" ? "합주" : "연습";
    const pageLabel = target?.book
        ? `${target.book}${target?.page ? ` 쨌 p.${target.page}` : ""}`
        : target?.page
            ? `p.${target.page}`
            : "";
    const spotifyLabel = target?.spotifyUrl ? "Spotify" : "링크";
    const lickLabel = target?.lickFile ? "선택됨" : "Lick";

    if (!titleNode) {
        return;
    }

    titleNode.textContent = title;
    subtitleNode.textContent = bpm
        ? `${bpm} BPM · ${noteKind} 카드 · ${pageLabel || ""}`
        : `${noteKind} 카드 · ${pageLabel || ""}`;
    irealValue.textContent = title === "?좏깮???명듃 ?놁쓬" ? "?쒕ぉ" : title;
    goodnotesValue.textContent = pageLabel || "?낅낫";
    if (realbookValue) {
        realbookValue.textContent = target?.book ? "?닿린" : "?낅낫";
    }
    metro2Value.textContent = bpm ? `${bpm} BPM` : "BPM";
    metro4Value.textContent = bpm ? `${bpm} BPM` : "BPM";
    spotifyValue.textContent = spotifyLabel;
    if (lickValue) {
        lickValue.textContent = lickLabel;
    }
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
        lickFile: document.getElementById("practiceLickFileInput").value.trim(),
        rendererFile: document.getElementById("practiceRendererFileInput").value.trim(),
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
        lickFile: document.getElementById("ensembleLickFileInput").value.trim(),
        rendererFile: document.getElementById("ensembleRendererFileInput").value.trim(),
    };
}

function bindMobileTargetInputs() {
    [
        "practiceTuneInput",
        "practiceBpmInput",
        "practiceBookInput",
        "practicePageInput",
        "practiceSpotifyInput",
        "practiceLickFileInput",
        "practiceRendererFileInput",
        "ensembleTitleInput",
        "ensembleBpmInput",
        "ensembleBookInput",
        "ensemblePageInput",
        "ensembleSpotifyInput",
        "ensembleLickFileInput",
        "ensembleRendererFileInput",
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
    DAILY_STATE.metronome.pulseCount = 0;
    syncMetronomeButtons();
}

function ensureAudioContext() {
    if (!DAILY_STATE.metronome.audioContext) {
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const masterGain = context.createGain();

        masterGain.gain.value = 1;
        masterGain.connect(context.destination);

        DAILY_STATE.metronome.audioContext = context;
        DAILY_STATE.metronome.masterGain = masterGain;
    }

    return DAILY_STATE.metronome.audioContext;
}

async function ensureMetronomeAudioReady() {
    const context = ensureAudioContext();

    if (context.state === "suspended") {
        await context.resume();
    }

    if (!DAILY_STATE.metronome.unlocked) {
        const buffer = context.createBuffer(1, 1, 22050);
        const source = context.createBufferSource();

        source.buffer = buffer;
        source.connect(DAILY_STATE.metronome.masterGain || context.destination);
        source.start(0);
        source.stop(context.currentTime + 0.01);
        DAILY_STATE.metronome.unlocked = true;
    }

    return context;
}

function playClick() {
    const context = DAILY_STATE.metronome.audioContext || ensureAudioContext();
    const masterGain = DAILY_STATE.metronome.masterGain;
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const now = context.currentTime;

    oscillator.type = "square";
    oscillator.frequency.setValueAtTime(1850, now);
    oscillator.frequency.exponentialRampToValueAtTime(1450, now + 0.012);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.28, now + 0.0035);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.028);

    oscillator.connect(gain);
    gain.connect(masterGain || context.destination);
    oscillator.start(now);
    oscillator.stop(now + 0.03);
}

function tickMetronome() {
    playClick();
    DAILY_STATE.metronome.pulseCount += 1;
}

async function startMetronome(feelDivider) {
    const target = DAILY_STATE.activeMobileTarget;
    const bpm = parseInt(getMobileTargetBpm(target), 10);

    if (!bpm) {
        alert("현재 선택한 카드에 BPM이 없습니다.");
        return;
    }

    if (DAILY_STATE.metronome.feel === feelDivider) {
        stopMetronome();
        return;
    }

    stopMetronome();
    try {
        await ensureMetronomeAudioReady();
    } catch (error) {
        console.error("metronome resume failed", error);
        return;
    }

    const intervalMs = Math.max(120, (60000 / bpm) * feelDivider);

    DAILY_STATE.metronome.feel = feelDivider;
    DAILY_STATE.metronome.pulseCount = 0;
    tickMetronome();
    DAILY_STATE.metronome.timerId = window.setInterval(() => {
        tickMetronome();
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

async function openRealbookView(target) {
    const params = new URLSearchParams({
        book: target?.book || "",
        title: target?.title || "",
        page: target?.page || "",
    });

    const response = await fetch(`/music/realbook/resolve?${params.toString()}`);
    const result = await response.json();

    if (!response.ok || !result.success || !result.viewUrl) {
        alert(result.message || "?낅낫瑜?李얠? 紐삵뻽?듬땲??");
        return;
    }

    window.location.href = result.viewUrl;
}

function bindMobileToolButtons() {
    const tools = document.getElementById("practiceMobileTools");
    const irealButton = document.getElementById("mobileIrealButton");
    const metro2Button = document.getElementById("mobileMetro2Button");
    const metro4Button = document.getElementById("mobileMetro4Button");
    const goodnotesButton = document.getElementById("mobileGoodnotesButton");
    const realbookButton = document.getElementById("mobileRealbookButton");
    const spotifyButton = document.getElementById("mobileSpotifyButton");
    const lickButton = document.getElementById("mobileLickButton");
    const toggleButton = document.getElementById("mobileToolsToggleButton");

    if (!irealButton) {
        return;
    }

    if (toggleButton && tools) {
        toggleButton.addEventListener("click", () => {
            DAILY_STATE.mobileToolsCollapsed = !DAILY_STATE.mobileToolsCollapsed;
            tools.classList.toggle("is-collapsed", DAILY_STATE.mobileToolsCollapsed);
        toggleButton.textContent = DAILY_STATE.mobileToolsCollapsed ? "숨기기" : "열기";
            toggleButton.setAttribute("aria-expanded", DAILY_STATE.mobileToolsCollapsed ? "false" : "true");
        });
    }

    irealButton.addEventListener("click", () => {
        const title = encodeURIComponent(getMobileTargetTitle(DAILY_STATE.activeMobileTarget));

        if (!title || title === encodeURIComponent("?좏깮???명듃 ?놁쓬")) {
            return;
        }

        window.location.href = `irealb://search?${title}`;
    });

    metro2Button.addEventListener("click", () => startMetronome(2));
    metro4Button.addEventListener("click", () => startMetronome(1));

    goodnotesButton.addEventListener("click", () => {
        alert("Goodnotes 버튼은 아직 준비 중이에요. 연결 스키마만 먼저 둔 상태예요.");
    });

    if (realbookButton) {
        realbookButton.addEventListener("click", async () => {
            await openRealbookView(DAILY_STATE.activeMobileTarget);
        });
    }

    spotifyButton.addEventListener("click", () => {
        const url = DAILY_STATE.activeMobileTarget?.spotifyUrl;

        if (!url) {
            alert("현재 선택한 카드에 Spotify 링크가 없습니다.");
            return;
        }

        window.location.href = url;
    });

    if (lickButton) {
        lickButton.addEventListener("click", () => {
            const file = DAILY_STATE.activeMobileTarget?.lickFile;

            if (!file) {
                alert("현재 선택한 카드에 Lick MP3가 없습니다.");
                return;
            }

            window.location.href = `/music/licks?file=${encodeURIComponent(file)}`;
        });
    }
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
    document.getElementById("practiceLickFileInput").value = "";
    document.getElementById("practiceRendererFileInput").value = "";
    setSelectedPracticeTopics([]);
    setPracticeStatus("normal");
    document.getElementById("addPracticeCardButton").textContent = "+ 移대뱶 異붽?";
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
    document.getElementById("practiceLickFileInput").value = item.lickFile || "";
    document.getElementById("practiceRendererFileInput").value = item.rendererFile || "";
    setSelectedPracticeTopics(item.topics || []);
    setPracticeStatus(item.status || "normal");
    document.getElementById("addPracticeCardButton").textContent = "Update";
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
        lickFile: item.lickFile || "",
        rendererFile: item.rendererFile || "",
    });
}

function collectPracticePayload() {
    return {
        title: document.getElementById("practiceTuneInput").value.trim(),
        bpm: document.getElementById("practiceBpmInput").value.trim(),
        book: document.getElementById("practiceBookInput").value.trim(),
        page: document.getElementById("practicePageInput").value.trim(),
        spotifyUrl: document.getElementById("practiceSpotifyInput").value.trim(),
        lickFile: document.getElementById("practiceLickFileInput").value.trim(),
        rendererFile: document.getElementById("practiceRendererFileInput").value.trim(),
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
        lickFile: document.getElementById("ensembleLickFileInput").value.trim(),
        rendererFile: document.getElementById("ensembleRendererFileInput").value.trim(),
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
    document.getElementById("ensembleLickFileInput").value = "";
    document.getElementById("ensembleRendererFileInput").value = "";
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
        const mergeButton = fragment.querySelector(".practice-homework-merge-button");
        const remove = fragment.querySelector(".practice-homework-remove-button");

        note.dataset.homeworkId = item.id;
        title.textContent = item.title;
        body.textContent = item.memo;
        note.classList.toggle("is-merge-source", DAILY_STATE.draggedHomeworkId === item.id);

        body.addEventListener("blur", async () => {
            const report = await requestJson(`/music/daily/homework/${item.id}`, {
                method: "PUT",
                body: JSON.stringify({
                    title: item.title,
                    memo: body.textContent.trim(),
                }),
            });
            updateStateFromReport(report);
            renderAll();
        });

        mergeButton.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();

            if (DAILY_STATE.draggedHomeworkId === item.id) {
                clearHomeworkMergeState();
                renderAll();
                return;
            }

            DAILY_STATE.draggedHomeworkId = item.id;
            renderAll();
        });

        remove.addEventListener("click", async () => {
            if (!confirmDelete("???숈젣 移대뱶瑜???젣?좉퉴??")) {
                return;
            }

            const report = await requestJson(`/music/daily/homework/${item.id}`, {
                method: "DELETE",
            });
            updateStateFromReport(report);
            renderAll();
        });

        note.addEventListener("dragstart", () => {
            DAILY_STATE.draggedHomeworkId = item.id;
            note.classList.add("is-merge-source");
        });

        note.addEventListener("dragend", () => {
            clearHomeworkMergeState();
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

            const report = await mergeHomework(
                DAILY_STATE.draggedHomeworkId,
                item.id
            );

            clearHomeworkMergeState();
            updateStateFromReport(report);
            renderAll();
        });

        note.addEventListener("click", async (event) => {
            if (!DAILY_STATE.draggedHomeworkId || DAILY_STATE.draggedHomeworkId === item.id) {
                return;
            }

            if (event.target.closest(".practice-homework-note-body")) {
                return;
            }

            const report = await mergeHomework(
                DAILY_STATE.draggedHomeworkId,
                item.id
            );
            clearHomeworkMergeState();
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
    const lickFileInput = fragment.querySelector(".practice-inline-lick-file");
    const rendererFileInput = fragment.querySelector(".practice-inline-renderer-file");
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
    lickFileInput.value = item.lickFile || "";
    rendererFileInput.value = item.rendererFile || "";
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
                lickFile: lickFileInput.value.trim(),
                rendererFile: rendererFileInput.value.trim(),
                spotifyUrl: spotifyInput.value.trim(),
                status: statusInput.value.trim(),
                topics: topicsInput.value.trim(),
                memo: memoInput.value.trim(),
            }),
        });
        updateStateFromReport(report);
        renderAll();
    }

    [titleInput, bpmInput, bookInput, pageInput, statusInput, lickFileInput, rendererFileInput, spotifyInput, topicsInput, memoInput]
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
                    lickFile: lickFileInput.value.trim(),
                    rendererFile: rendererFileInput.value.trim(),
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
                    lickFile: lickFileInput.value.trim(),
                    rendererFile: rendererFileInput.value.trim(),
                    spotifyUrl: spotifyInput.value.trim(),
                });
            });
        });

    removeButton.addEventListener("click", async () => {
        if (!confirmDelete("이 합주 카드를 삭제할까요?")) {
            return;
        }

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
        fragment.querySelector(".practice-summary-title").textContent = item.title || "제목 없는 연습";
        fragment.querySelector(".practice-summary-topline").textContent = item.page
            ? `${item.book || "Book"} / p.${item.page}`
            : item.book || "Book";
        fragment.querySelector(".practice-summary-status").textContent = getStatusLabel(item.status);
        fragment.querySelector(".practice-summary-status").className = `practice-summary-status practice-summary-status-${item.status || "normal"}`;
        fragment.querySelector(".practice-summary-bpm").textContent = item.bpm ? `${item.bpm} BPM` : "BPM 없음";
        fragment.querySelector(".practice-summary-book").textContent = (item.topics || []).length
            ? item.topics.map((topic) => `#${topic}`).join(" ")
            : "Topics none";
        fragment.querySelector(".practice-summary-metro").className = `practice-summary-metro ${hasMetronome ? "hidden" : ""}`;
        fragment.querySelector(".practice-summary-topics").textContent = item.memo || "?쒖쨪 ???놁쓬";
        fragment.querySelector(".practice-summary-memo").textContent = buildPracticeMeta(item) || "?낅낫 ?뺣낫 ?놁쓬";

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
                lickFile: item.lickFile || "",
                rendererFile: item.rendererFile || "",
            });
            fillPracticeForm(item);
        });

        removeButton.addEventListener("click", async (event) => {
            event.stopPropagation();
            if (!confirmDelete("이 연습 카드를 삭제할까요?")) {
                return;
            }
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
    renderCurrentArchive();
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
    bindTapOutsideBlur();

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
window.addEventListener("lick-settings-change", () => {
    const dateNode = document.getElementById("practiceDailyDate");

    if (dateNode) {
        dateNode.textContent = formatDailyDate();
    }

    renderAll();
});
window.addEventListener("pagehide", stopMetronome);
document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        stopMetronome();
    }
});











