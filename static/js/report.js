const REPORT_STATE = {
    days: [],
    weeks: [],
    selectedWeekKey: "",
    activeMobileTarget: null,
    metronome: {
        audioContext: null,
        masterGain: null,
        timerId: null,
        feel: null,
        unlocked: false,
    },
    mobileToolsCollapsed: false,
};

function loadReportData() {
    const node = document.getElementById("report-calendar-data");

    if (!node) {
        return { days: [], weeks: [] };
    }

    try {
        return JSON.parse(node.textContent);
    } catch (error) {
        console.error(error);
        return { days: [], weeks: [] };
    }
}

function getLevelClass(level) {
    if (level < 0) {
        return "report-cell-bad";
    }

    return `report-cell-l${level}`;
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

    const toneClass = item.status === "bad" || !item.metronome
        ? "practice-report-item-bad"
        : item.status === "good"
            ? "practice-report-item-good"
            : "";

    return `
        <article
            class="practice-report-item practice-mobile-target-card ${toneClass}"
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

function getMobileTargetTitle(target) {
    return target?.title?.trim() || "선택된 제목 없음";
}

function getMobileTargetBpm(target) {
    return target?.bpm?.trim() || "";
}

function buildTargetFromDataset(node) {
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

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || `request failed: ${response.status}`);
    }

    return data;
}

function syncMetronomeButtons() {
    const metro2Button = document.getElementById("mobileMetro2Button");
    const metro4Button = document.getElementById("mobileMetro4Button");

    if (!metro2Button || !metro4Button) {
        return;
    }

    metro2Button.classList.toggle("is-active", REPORT_STATE.metronome.feel === 2);
    metro4Button.classList.toggle("is-active", REPORT_STATE.metronome.feel === 1);
}

function updateMobileToolState() {
    const titleNode = document.getElementById("mobileToolTitle");
    const subtitleNode = document.getElementById("mobileToolSubtitle");
    const lickValue = document.getElementById("mobileLickValue");
    const realbookValue = document.getElementById("mobileRealbookValue");
    const target = REPORT_STATE.activeMobileTarget;
    const title = getMobileTargetTitle(target);
    const bpm = getMobileTargetBpm(target);
    const noteKind = target?.kind === "ensemble" ? "합주" : "연습";
    const pageLabel = target?.book
        ? `${target.book}${target?.page ? ` · p.${target.page}` : ""}`
        : target?.page
            ? `p.${target.page}`
            : "";

    if (!titleNode || !subtitleNode) {
        return;
    }

    titleNode.textContent = title;
    subtitleNode.textContent = bpm
        ? `${bpm} BPM · ${noteKind} 카드 기준${pageLabel ? ` · ${pageLabel}` : ""}`
        : `${noteKind} 카드 기준${pageLabel ? ` · ${pageLabel}` : ""}`;
    if (realbookValue) {
        realbookValue.textContent = target?.book ? "?닿린" : "?낅낫";
    }
    if (lickValue) {
        lickValue.textContent = target?.lickFile ? "Selected" : "Lick";
    }
    syncMetronomeButtons();
}

function setActiveMobileTarget(target) {
    REPORT_STATE.activeMobileTarget = target;
    updateMobileToolState();
}

function ensureAudioContext() {
    if (!REPORT_STATE.metronome.audioContext) {
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const masterGain = context.createGain();

        masterGain.gain.value = 1;
        masterGain.connect(context.destination);

        REPORT_STATE.metronome.audioContext = context;
        REPORT_STATE.metronome.masterGain = masterGain;
    }

    return REPORT_STATE.metronome.audioContext;
}

async function ensureMetronomeAudioReady() {
    const context = ensureAudioContext();

    if (context.state === "suspended") {
        await context.resume();
    }

    if (!REPORT_STATE.metronome.unlocked) {
        const buffer = context.createBuffer(1, 1, 22050);
        const source = context.createBufferSource();

        source.buffer = buffer;
        source.connect(REPORT_STATE.metronome.masterGain || context.destination);
        source.start(0);
        source.stop(context.currentTime + 0.01);
        REPORT_STATE.metronome.unlocked = true;
    }
}

function playClick() {
    const context = REPORT_STATE.metronome.audioContext || ensureAudioContext();
    const masterGain = REPORT_STATE.metronome.masterGain;
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

function stopMetronome() {
    if (REPORT_STATE.metronome.timerId) {
        clearInterval(REPORT_STATE.metronome.timerId);
    }

    REPORT_STATE.metronome.timerId = null;
    REPORT_STATE.metronome.feel = null;
    syncMetronomeButtons();
}

async function startMetronome(feelDivider) {
    const bpm = parseInt(getMobileTargetBpm(REPORT_STATE.activeMobileTarget), 10);

    if (!bpm) {
        alert("선택한 카드에 BPM이 없습니다.");
        return;
    }

    if (REPORT_STATE.metronome.feel === feelDivider) {
        stopMetronome();
        return;
    }

    stopMetronome();
    await ensureMetronomeAudioReady();

    const intervalMs = Math.max(120, (60000 / bpm) * feelDivider);

    REPORT_STATE.metronome.feel = feelDivider;
    playClick();
    REPORT_STATE.metronome.timerId = window.setInterval(playClick, intervalMs);
    syncMetronomeButtons();
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
        alert(result.message || "정보를 찾지 못했습니다.");
        return;
    }

    window.location.href = result.viewUrl;
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

    await requestJson(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
    });

    REPORT_STATE.activeMobileTarget = target;
    updateMobileToolState();
    alert("등록된 숙제가 없습니다.");
}

function bindMobileToolButtons() {
    const tools = document.getElementById("reportMobileTools");
    const toggleButton = document.getElementById("mobileToolsToggleButton");
    const irealButton = document.getElementById("mobileIrealButton");
    const metro2Button = document.getElementById("mobileMetro2Button");
    const metro4Button = document.getElementById("mobileMetro4Button");
    const goodnotesButton = document.getElementById("mobileGoodnotesButton");
    const realbookButton = document.getElementById("mobileRealbookButton");
    const spotifyButton = document.getElementById("mobileSpotifyButton");
    const lickButton = document.getElementById("mobileLickButton");

    if (!tools || !toggleButton) {
        return;
    }

    toggleButton.addEventListener("click", () => {
        REPORT_STATE.mobileToolsCollapsed = !REPORT_STATE.mobileToolsCollapsed;
        tools.classList.toggle("is-collapsed", REPORT_STATE.mobileToolsCollapsed);
        toggleButton.textContent = REPORT_STATE.mobileToolsCollapsed ? "Hide" : "Open";
        toggleButton.setAttribute("aria-expanded", REPORT_STATE.mobileToolsCollapsed ? "false" : "true");
    });

    irealButton.addEventListener("click", () => {
        const title = encodeURIComponent(getMobileTargetTitle(REPORT_STATE.activeMobileTarget));

        if (!title || title === encodeURIComponent("선택된 노트 없음")) {
            return;
        }

        window.location.href = `irealb://search?${title}`;
    });

    metro2Button.addEventListener("click", () => startMetronome(2));
    metro4Button.addEventListener("click", () => startMetronome(1));

    goodnotesButton.addEventListener("click", () => {
        alert("Goodnotes 버튼은 준비만 해두었어요.");
    });

    if (realbookButton) {
        realbookButton.addEventListener("click", async () => {
            await openRealbookView(REPORT_STATE.activeMobileTarget);
        });
    }

    spotifyButton.addEventListener("click", () => {
        const url = REPORT_STATE.activeMobileTarget?.spotifyUrl;

        if (!url) {
            alert("선택한 카드에 Spotify 링크가 없습니다.");
            return;
        }

        window.location.href = url;
    });

    if (lickButton) {
        lickButton.addEventListener("click", () => {
            const file = REPORT_STATE.activeMobileTarget?.lickFile;

            if (!file) {
                alert("선택한 카드에 Lick MP3가 없습니다.");
                return;
            }

            window.location.href = `/music/licks?file=${encodeURIComponent(file)}`;
        });
    }
}

function renderWeekdays() {
    const node = document.getElementById("reportWeekdays");

    if (!node) {
        return;
    }

    node.innerHTML = LickSettings.getWeekdayLabels()
        .map((weekday) => `<div class="report-weekday">${weekday}</div>`)
        .join("");
}

function renderReportCalendar() {
    const container = document.getElementById("reportCalendar");

    if (!container) {
        return;
    }

    const leadingEmpty = REPORT_STATE.days.length
        ? REPORT_STATE.days[0].weekdayIndex || 0
        : 0;

    const emptyCells = Array.from({ length: leadingEmpty }, () => "<div class='report-cell report-cell-empty'></div>");
    const filledCells = REPORT_STATE.days.map((day) => `
        <button
            type="button"
            class="report-cell ${getLevelClass(day.level)}"
            data-week-key="${day.weekKey || ""}"
            title="${LickSettings.formatDateLabel(day.date) || day.date} / solo ${day.soloCount} / ensemble ${day.ensembleCount}"
        >
            <span class="report-cell-day">${(LickSettings.formatDateLabel(day.date) || day.date).slice(-2)}</span>
        </button>
    `);

    container.innerHTML = emptyCells.concat(filledCells).join("");

    container.querySelectorAll(".report-cell[data-week-key]").forEach((button) => {
        button.addEventListener("click", () => {
            const weekKey = button.dataset.weekKey || "";

            if (!weekKey) {
                return;
            }

            REPORT_STATE.selectedWeekKey = weekKey;
            renderWeekList();
            renderSelectedWeek();
        });
    });
}

function renderWeekList() {
    const node = document.getElementById("reportWeekList");

    if (!node) {
        return;
    }

    node.innerHTML = REPORT_STATE.weeks.map((week) => `
        <button
            type="button"
            class="report-week-button ${REPORT_STATE.selectedWeekKey === week.weekKey ? "is-selected" : ""}"
            data-week-key="${week.weekKey}"
        >
            <span class="report-week-button-title">${week.weekLabel}</span>
            <span class="report-week-button-meta">숙제 ${week.homeworkCount} · 합주 ${week.ensembleCount} · 연습 ${week.practiceCount}</span>
        </button>
    `).join("");

    node.querySelectorAll(".report-week-button").forEach((button) => {
        button.addEventListener("click", () => {
            REPORT_STATE.selectedWeekKey = button.dataset.weekKey || "";
            renderWeekList();
            renderSelectedWeek();
        });
    });
}

function renderSelectedWeek() {
    const selectedWeek = REPORT_STATE.weeks.find(
        (week) => week.weekKey === REPORT_STATE.selectedWeekKey
    ) || REPORT_STATE.weeks[0];
    const titleNode = document.getElementById("selectedWeekTitle");
    const metaNode = document.getElementById("selectedWeekMeta");
    const homeworkNode = document.getElementById("reportHomeworkList");
    const daysNode = document.getElementById("reportArchiveDays");

    if (!selectedWeek || !titleNode || !metaNode || !homeworkNode || !daysNode) {
        return;
    }

    titleNode.textContent = selectedWeek.weekLabel;
    metaNode.textContent = `숙제 ${selectedWeek.homeworkCount} · 합주 ${selectedWeek.ensembleCount} · 연습 ${selectedWeek.practiceCount}`;

    if (selectedWeek.homework.length === 0) {
        homeworkNode.innerHTML = "<div class='practice-report-empty'>이번 주에 숙제가 없습니다.</div>";
    } else {
        homeworkNode.innerHTML = selectedWeek.homework.map((item) => `
            <article class="practice-report-item">
                <div class="practice-report-item-title">${item.title}</div>
                <div class="practice-report-item-copy">${item.memo || "메모 없음"}</div>
            </article>
        `).join("");
    }

    daysNode.innerHTML = selectedWeek.dailyBuckets.map((day) => `
        <section class="practice-report-day ${day.isBad ? "practice-report-day-bad" : ""}">
            <div class="practice-report-day-head">
                <div class="practice-report-day-title">${day.weekday}</div>
                <div class="practice-report-day-meta">${day.label}</div>
            </div>
            ${
                day.isEmpty
                    ? "<div class='practice-report-empty'>연습 카드가 없습니다.</div>"
                    : `
                        <div class="practice-report-day-list">
                            ${day.practice.map((item) => buildArchiveItemMarkup(item, "practice")).join("")}
                            ${day.ensemble.map((item) => buildArchiveItemMarkup(item, "ensemble")).join("")}
                        </div>
                    `
            }
        </section>
    `).join("");

    daysNode.querySelectorAll(".practice-mobile-target-card").forEach((card) => {
        card.addEventListener("click", async () => {
            if (!window.confirm("이 연습 카드를 복제할까요?")) {
                return;
            }

            await duplicateArchiveTarget(buildTargetFromDataset(card));
        });
    });
}

function initReportPage() {
    const data = loadReportData();

    REPORT_STATE.days = data.days || [];
    REPORT_STATE.weeks = data.weeks || [];
    REPORT_STATE.selectedWeekKey = REPORT_STATE.weeks[0]?.weekKey || "";

    renderWeekdays();
    renderReportCalendar();
    renderWeekList();
    renderSelectedWeek();
    bindMobileToolButtons();
    updateMobileToolState();
}

document.addEventListener("DOMContentLoaded", initReportPage);
window.addEventListener("lick-settings-change", () => {
    renderWeekdays();
    renderReportCalendar();
    renderWeekList();
    renderSelectedWeek();
});
window.addEventListener("pagehide", stopMetronome);
document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        stopMetronome();
    }
});



