const INSIGHT_LABELS = {
    rhythm: "리듬",
    solo: "솔로",
    ensemble: "합주",
    voicing: "보이싱",
};

let INSIGHT_STATE = {};

function loadInsightState() {
    const node = document.getElementById("insight-data");

    if (!node) {
        INSIGHT_STATE = {};
        return;
    }

    try {
        INSIGHT_STATE = JSON.parse(node.textContent);
    } catch (error) {
        console.error(error);
        INSIGHT_STATE = {};
    }
}

async function requestInsight(url, options = {}) {
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

function renderInsightColumns() {
    const container = document.getElementById("insightColumns");

    if (!container) {
        return;
    }

    container.innerHTML = Object.entries(INSIGHT_LABELS).map(([category, label]) => {
        const items = INSIGHT_STATE[category] || [];

        return `
            <article class="card insight-column">
                <div class="section-title-row">
                    <h2>${label}</h2>
                    <span class="section-count">${items.length}개</span>
                </div>
                <div class="insight-list">
                    ${items.length ? items.map((item) => `
                        <article class="insight-item" data-category="${category}" data-insight-id="${item.id}">
                            <input class="insight-item-title" type="text" value="${item.title || ""}">
                            <textarea class="insight-item-memo">${item.memo || ""}</textarea>
                            <div class="practice-editor-actions">
                                <button type="button" class="danger-button insight-delete-button">삭제</button>
                            </div>
                        </article>
                    `).join("") : '<div class="practice-report-empty">아직 저장된 인사이트가 없습니다.</div>'}
                </div>
            </article>
        `;
    }).join("");

    bindInsightEvents();
}

function bindInsightEvents() {
    document.querySelectorAll(".insight-item").forEach((itemNode) => {
        const category = itemNode.dataset.category;
        const insightId = itemNode.dataset.insightId;
        const titleInput = itemNode.querySelector(".insight-item-title");
        const memoInput = itemNode.querySelector(".insight-item-memo");
        const deleteButton = itemNode.querySelector(".insight-delete-button");

        async function saveInsight() {
            INSIGHT_STATE = await requestInsight(`/music/insights/${category}/${insightId}`, {
                method: "PUT",
                body: JSON.stringify({
                    title: titleInput.value.trim(),
                    memo: memoInput.value.trim(),
                }),
            });
            renderInsightColumns();
        }

        titleInput.addEventListener("blur", saveInsight);
        memoInput.addEventListener("blur", saveInsight);

        deleteButton.addEventListener("click", async () => {
            INSIGHT_STATE = await requestInsight(`/music/insights/${category}/${insightId}`, {
                method: "DELETE",
            });
            renderInsightColumns();
        });
    });
}

function resetInsightEditor() {
    document.getElementById("insightCategoryInput").value = "rhythm";
    document.getElementById("insightTitleInput").value = "";
    document.getElementById("insightMemoInput").value = "";
}

async function addInsight() {
    const category = document.getElementById("insightCategoryInput").value;
    const title = document.getElementById("insightTitleInput").value.trim();
    const memo = document.getElementById("insightMemoInput").value.trim();

    if (!title && !memo) {
        return;
    }

    INSIGHT_STATE = await requestInsight("/music/insights", {
        method: "POST",
        body: JSON.stringify({ category, title, memo }),
    });
    resetInsightEditor();
    renderInsightColumns();
}

function initInsightsPage() {
    if (!document.getElementById("insightColumns")) {
        return;
    }

    loadInsightState();
    renderInsightColumns();
    document.getElementById("addInsightButton").addEventListener("click", addInsight);
}

document.addEventListener("DOMContentLoaded", initInsightsPage);
