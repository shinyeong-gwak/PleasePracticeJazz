function loadRealbookViewerData() {
    const node = document.getElementById("realbook-viewer-data");

    if (!node) {
        return null;
    }

    try {
        return JSON.parse(node.textContent);
    } catch (error) {
        console.error("realbook viewer parse error", error);
        return null;
    }
}

function setViewerMessage(message, isError = false) {
    const node = document.getElementById("realbookViewerMessage");

    if (!node) {
        return;
    }

    node.textContent = message;
    node.hidden = false;
    node.dataset.state = isError ? "error" : "info";
}

function hideViewerMessage() {
    const node = document.getElementById("realbookViewerMessage");

    if (!node) {
        return;
    }

    node.hidden = true;
}

async function renderRealbookPage() {
    const data = loadRealbookViewerData();
    const canvas = document.getElementById("realbookCanvas");

    if (!data || !canvas) {
        setViewerMessage("PDF 뷰어 정보를 찾지 못했습니다.", true);
        return;
    }

    if (!window.pdfjsLib) {
        setViewerMessage("PDF 뷰어 라이브러리를 불러오지 못했습니다.", true);
        return;
    }

    try {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc =
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

        const loadingTask = window.pdfjsLib.getDocument({
            url: data.fileUrl,
            cMapPacked: true,
        });
        const pdf = await loadingTask.promise;
        const pageNumber = Math.max(1, parseInt(data.page, 10) || 1);
        const page = await pdf.getPage(pageNumber);
        const shell = canvas.parentElement;
        const baseViewport = page.getViewport({ scale: 1 });
        const shellWidth = Math.max(320, (shell?.clientWidth || baseViewport.width) - 24);
        const scale = shellWidth / baseViewport.width;
        const viewport = page.getViewport({ scale });
        const context = canvas.getContext("2d");

        if (!context) {
            throw new Error("canvas context unavailable");
        }

        canvas.width = Math.ceil(viewport.width);
        canvas.height = Math.ceil(viewport.height);
        canvas.style.width = `${Math.ceil(viewport.width)}px`;
        canvas.style.height = `${Math.ceil(viewport.height)}px`;

        await page.render({
            canvasContext: context,
            viewport,
        }).promise;

        hideViewerMessage();
    } catch (error) {
        console.error("realbook render error", error);
        setViewerMessage("PDF 페이지를 렌더하지 못했습니다. 'PDF 열기' 버튼으로 원본을 확인해 주세요.", true);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    void renderRealbookPage();
});
