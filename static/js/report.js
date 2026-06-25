function loadReportData() {
    const node = document.getElementById("report-calendar-data");

    if (!node) {
        return { days: [] };
    }

    try {
        return JSON.parse(node.textContent);
    } catch (error) {
        console.error(error);
        return { days: [] };
    }
}

function getLevelClass(level) {
    if (level < 0) {
        return "report-cell-bad";
    }

    return `report-cell-l${level}`;
}

function renderReportCalendar() {
    const container = document.getElementById("reportCalendar");
    const { days } = loadReportData();

    if (!container) {
        return;
    }

    container.innerHTML = days.map((day) => `
        <div class="report-cell ${getLevelClass(day.level)}" title="${day.date} / solo ${day.soloCount} / ensemble ${day.ensembleCount}">
            <span class="report-cell-day">${day.date.slice(8)}</span>
        </div>
    `).join("");
}

document.addEventListener("DOMContentLoaded", renderReportCalendar);
