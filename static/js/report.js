const REPORT_STATE = {
    days: [],
    weeks: [],
    selectedWeekKey: "",
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
        <article class="practice-report-item ${toneClass}">
            <div class="practice-report-item-title">${item.title || (kind === "ensemble" ? "이름 없는 합주 노트" : "이름 없는 연습")}</div>
            <div class="practice-report-item-meta">${kind === "ensemble" ? "합주" : "연습"}${meta.length ? ` · ${meta.join(" · ")}` : ""}</div>
            <div class="practice-report-item-copy">${item.memo || "메모 없음"}</div>
        </article>
    `;
}

function renderWeekdays() {
    const node = document.getElementById("reportWeekdays");

    if (!node) {
        return;
    }

    node.innerHTML = ["월", "화", "수", "목", "금", "토", "일"]
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
            title="${day.date} / solo ${day.soloCount} / ensemble ${day.ensembleCount}"
        >
            <span class="report-cell-day">${day.date.slice(8)}</span>
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
        homeworkNode.innerHTML = "<div class='practice-report-empty'>이 주에는 숙제가 없습니다.</div>";
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
}

document.addEventListener("DOMContentLoaded", initReportPage);
