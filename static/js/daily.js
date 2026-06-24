const DAILY_TOPICS = [
    "박자",
    "테크닉",
    "톤",
    "보이싱",
    "스케일",
    "카피"
];

const DAILY_STATE = {
    weekLabel: "",
    homework: [],
    practice: []
};

function formatDailyDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = `${today.getMonth() + 1}`.padStart(2, "0");
    const date = `${today.getDate()}`.padStart(2, "0");

    return `${year}.${month}.${date}`;
}

function loadInitialReport() {
    const node = document.getElementById("daily-report-data");

    if (!node) {
        return;
    }

    try {
        const payload = JSON.parse(node.textContent);
        DAILY_STATE.weekLabel = payload.weekLabel || "";
        DAILY_STATE.homework = payload.homework || [];
        DAILY_STATE.practice = payload.practice || [];
    } catch (error) {
        console.error("daily report parse error", error);
    }
}

function updateTopicValue(card) {
    const selectedTopics = Array.from(
        card.querySelectorAll(".practice-topic-chip.is-selected")
    ).map((button) => button.dataset.topic)
        .filter((topic) => DAILY_TOPICS.includes(topic));

    const hiddenInput = card.querySelector(".practice-topic-value");

    if (hiddenInput) {
        hiddenInput.value = selectedTopics.join(",");
    }
}

function bindTopicButtons(scope) {
    const topicButtons = scope.querySelectorAll(".practice-topic-chip");

    topicButtons.forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.toggle("is-selected");
            updateTopicValue(scope);
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

            if (input) {
                input.value = button.dataset.status || "normal";
            }
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

function getHomeworkValues() {
    return {
        title: document.getElementById("practiceHomeworkTitleInput").value.trim(),
        memo: document.getElementById("practiceHomeworkMemoInput").value.trim()
    };
}

function getEditorValues() {
    const editor = document.getElementById("practiceEditorCard");
    const topicButtons = editor.querySelectorAll(".practice-topic-chip.is-selected");

    return {
        topics: Array.from(topicButtons).map((button) => button.dataset.topic),
        bpm: document.getElementById("practiceBpmInput").value.trim(),
        title: document.getElementById("practiceTuneInput").value.trim(),
        book: document.getElementById("practiceBookInput").value.trim(),
        page: document.getElementById("practicePageInput").value.trim(),
        status: document.getElementById("practiceStatusInput").value.trim() || "normal",
        memo: document.getElementById("practiceMemoInput").value.trim()
    };
}

function resetHomeworkEditor() {
    document.getElementById("practiceHomeworkTitleInput").value = "";
    document.getElementById("practiceHomeworkMemoInput").value = "";
}

function resetEditor() {
    document.getElementById("practiceBpmInput").value = "";
    document.getElementById("practiceTuneInput").value = "";
    document.getElementById("practiceBookInput").value = "";
    document.getElementById("practicePageInput").value = "";
    document.getElementById("practiceMemoInput").value = "";
    document.getElementById("practiceTopicValue").value = "";
    document.getElementById("practiceStatusInput").value = "normal";

    document.querySelectorAll("#practiceEditorCard .practice-topic-chip").forEach((button) => {
        button.classList.remove("is-selected");
    });
    document.querySelectorAll(".practice-status-chip").forEach((button) => {
        button.classList.toggle("is-selected", button.dataset.status === "normal");
    });
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

function renderHomeworkReport() {
    const list = document.getElementById("practiceReportHomeworkList");

    if (!list) {
        return;
    }

    if (DAILY_STATE.homework.length === 0) {
        list.innerHTML = "<div class='practice-report-empty'>아직 등록된 숙제가 없습니다.</div>";
        return;
    }

    list.innerHTML = DAILY_STATE.homework.map((item) => `
        <article class="practice-report-item">
            <div class="practice-report-item-title">${item.title}</div>
            <div class="practice-report-item-copy">${item.memo}</div>
        </article>
    `).join("");
}

function renderPracticeReport() {
    const list = document.getElementById("practiceReportPracticeList");

    if (!list) {
        return;
    }

    if (DAILY_STATE.practice.length === 0) {
        list.innerHTML = "<div class='practice-report-empty'>아직 추가된 연습 카드가 없습니다.</div>";
        return;
    }

    list.innerHTML = DAILY_STATE.practice.map((item) => `
        <article class="practice-report-item practice-report-item-${item.status || "normal"}">
            <div class="practice-report-item-title">${item.title || "이름 없는 연습"}</div>
            <div class="practice-report-item-meta">${getStatusLabel(item.status)}</div>
            <div class="practice-report-item-meta">${buildPracticeMeta(item) || "정보 없음"}</div>
            <div class="practice-report-item-copy">${item.memo || (item.topics || []).map((topic) => `#${topic}`).join(" ") || "메모 없음"}</div>
        </article>
    `).join("");
}

function renderHomeworkBoard() {
    const board = document.getElementById("practiceHomeworkBoard");
    const template = document.getElementById("practiceHomeworkTemplate");

    if (!board || !template) {
        return;
    }

    board.innerHTML = "";

    DAILY_STATE.homework.forEach((item) => {
        const fragment = template.content.cloneNode(true);
        const note = fragment.querySelector(".practice-homework-note");

        note.dataset.homeworkId = item.id;
        note.querySelector(".practice-homework-note-title").textContent = item.title;
        note.querySelector(".practice-homework-note-body").textContent = item.memo;
        bindHomeworkRemoveButton(note);
        board.appendChild(fragment);
    });
}

function renderPracticeCards() {
    const cards = document.getElementById("practiceCards");
    const template = document.getElementById("practiceCardTemplate");

    if (!cards || !template) {
        return;
    }

    cards.innerHTML = "";

    DAILY_STATE.practice.forEach((item) => {
        const fragment = template.content.cloneNode(true);
        const card = fragment.querySelector(".practice-card");
        const topline = card.querySelector(".practice-summary-topline");
        const status = card.querySelector(".practice-summary-status");
        const bpm = card.querySelector(".practice-summary-bpm");
        const book = card.querySelector(".practice-summary-book");
        const topics = card.querySelector(".practice-summary-topics");
        const memo = card.querySelector(".practice-summary-memo");

        card.dataset.practiceId = item.id;
        card.classList.toggle("practice-summary-card-bad", item.status === "bad");
        card.classList.toggle("practice-summary-card-good", item.status === "good");
        card.querySelector(".practice-summary-title").textContent = item.title || "이름 없는 연습";
        topline.textContent = item.page
            ? `${item.book || "악보집 미지정"} · p.${item.page}`
            : item.book || "악보집 미지정";

        status.textContent = getStatusLabel(item.status);
        status.className = `practice-summary-status practice-summary-status-${item.status || "normal"}`;
        bpm.textContent = item.bpm ? `${item.bpm} BPM` : "BPM 없음";
        bpm.classList.toggle("is-missing", !item.bpm);

        book.textContent = (item.topics || []).length
            ? item.topics.map((topic) => `#${topic}`).join(" ")
            : "주제 미지정";

        topics.textContent = item.memo || "한줄 평 없음";
        memo.textContent = item.book || item.page
            ? `악보 정보: ${item.book || "미지정"}${item.page ? ` / ${item.page}p` : ""}`
            : "악보 정보 없음";

        bindRemoveButton(card);
        cards.appendChild(fragment);
    });
}

function renderAll() {
    renderHomeworkBoard();
    renderPracticeCards();
    renderHomeworkReport();
    renderPracticeReport();
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        throw new Error(`request failed: ${response.status}`);
    }

    return response.json();
}

async function deleteJson(url) {
    const response = await fetch(url, {
        method: "DELETE"
    });

    if (!response.ok) {
        throw new Error(`request failed: ${response.status}`);
    }

    return response.json();
}

function bindHomeworkRemoveButton(note) {
    const removeButton = note.querySelector(".practice-homework-remove-button");

    if (!removeButton) {
        return;
    }

    removeButton.addEventListener("click", async () => {
        const { homeworkId } = note.dataset;

        try {
            const result = await deleteJson(`/music/daily/homework/${homeworkId}`);

            if (!result.success) {
                return;
            }

            DAILY_STATE.homework = DAILY_STATE.homework.filter((item) => item.id !== homeworkId);
            renderAll();
        } catch (error) {
            console.error(error);
            alert("숙제 삭제에 실패했습니다.");
        }
    });
}

function bindRemoveButton(card) {
    const removeButton = card.querySelector(".practice-remove-button");

    if (!removeButton) {
        return;
    }

    removeButton.addEventListener("click", async () => {
        const { practiceId } = card.dataset;

        try {
            const result = await deleteJson(`/music/daily/practice/${practiceId}`);

            if (!result.success) {
                return;
            }

            DAILY_STATE.practice = DAILY_STATE.practice.filter((item) => item.id !== practiceId);
            renderAll();
        } catch (error) {
            console.error(error);
            alert("연습 카드 삭제에 실패했습니다.");
        }
    });
}

async function createHomeworkNote() {
    const values = getHomeworkValues();

    if (!values.title && !values.memo) {
        return;
    }

    try {
        const item = await postJson("/music/daily/homework", values);
        DAILY_STATE.homework.unshift(item);
        resetHomeworkEditor();
        renderAll();
    } catch (error) {
        console.error(error);
        alert("숙제 저장에 실패했습니다.");
    }
}

async function createPracticeCard() {
    const values = getEditorValues();

    try {
        const item = await postJson("/music/daily/practice", values);
        DAILY_STATE.practice.push(item);
        resetEditor();
        renderAll();

        const cards = document.getElementById("practiceCards");

        if (cards) {
            cards.scrollLeft = cards.scrollWidth;
        }
    } catch (error) {
        console.error(error);
        alert("연습 카드 저장에 실패했습니다.");
    }
}

function initPracticeDailyPage() {
    const addButton = document.getElementById("addPracticeCardButton");
    const addHomeworkButton = document.getElementById("addHomeworkButton");
    const dateNode = document.getElementById("practiceDailyDate");
    const weekNode = document.getElementById("practiceReportWeekLabel");
    const editor = document.getElementById("practiceEditorCard");

    if (!addButton || !editor) {
        return;
    }

    loadInitialReport();

    if (dateNode) {
        dateNode.textContent = formatDailyDate();
    }

    if (weekNode) {
        weekNode.textContent = DAILY_STATE.weekLabel || "이번주 Report";
    }

    bindTopicButtons(editor);
    bindStatusButtons();
    addButton.addEventListener("click", createPracticeCard);

    if (addHomeworkButton) {
        addHomeworkButton.addEventListener("click", createHomeworkNote);
    }

    renderAll();
}

document.addEventListener("DOMContentLoaded", initPracticeDailyPage);
