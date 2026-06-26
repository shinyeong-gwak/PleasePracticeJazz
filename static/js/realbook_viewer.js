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

async function renderRealbookPage() {
    const data = loadRealbookViewerData();
    const canvas = document.getElementById("realbookCanvas");

    if (!data || !canvas || !window.pdfjsLib) {
        return;
    }

    window.pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.5.136/pdf.worker.min.js";

    const loadingTask = window.pdfjsLib.getDocument(data.fileUrl);
    const pdf = await loadingTask.promise;
    const pageNumber = Math.max(1, parseInt(data.page, 10) || 1);
    const page = await pdf.getPage(pageNumber);
    const shell = canvas.parentElement;
    const baseViewport = page.getViewport({scale: 1});
    const shellWidth = shell?.clientWidth || baseViewport.width;
    const scale = Math.max(1, shellWidth / baseViewport.width);
    const viewport = page.getViewport({scale});
    const context = canvas.getContext("2d");

    canvas.width = viewport.width;
    canvas.height = viewport.height;
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    await page.render({
        canvasContext: context,
        viewport
    }).promise;
}

document.addEventListener("DOMContentLoaded", () => {
    void renderRealbookPage();
});
