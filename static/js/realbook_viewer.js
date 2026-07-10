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

function isNativePdfPreferred() {
    const userAgent = navigator.userAgent || "";
    const touchMac = navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;

    return /iPhone|iPad|iPod|Android/iu.test(userAgent) || touchMac;
}

function setViewerStatus(message) {
    const node = document.getElementById("realbookViewerStatus");

    if (!node) {
        return;
    }

    node.textContent = message;
}

function mountEmbeddedPdf(directUrl) {
    const objectNode = document.getElementById("realbookViewerObject");

    if (!objectNode) {
        return;
    }

    objectNode.data = directUrl;
    objectNode.classList.remove("hidden");
    setViewerStatus("PDF가 보이지 않으면 위의 'PDF 열기' 버튼을 눌러주세요.");
}

function redirectToNativePdf(directUrl) {
    setViewerStatus("기기 PDF 뷰어로 여는 중입니다. 잠시만 기다려주세요.");
    window.location.replace(directUrl);
}

function initRealbookViewer() {
    const data = loadRealbookViewerData();

    if (!data?.directUrl) {
        setViewerStatus("PDF 뷰어 정보를 찾지 못했습니다.");
        return;
    }

    const openButton = document.getElementById("realbookOpenButton");
    const fallbackButton = document.getElementById("realbookFallbackButton");

    if (openButton) {
        openButton.href = data.directUrl;
    }

    if (fallbackButton) {
        fallbackButton.href = data.directUrl;
    }

    if (isNativePdfPreferred()) {
        redirectToNativePdf(data.directUrl);
        return;
    }

    mountEmbeddedPdf(data.directUrl);
}

document.addEventListener("DOMContentLoaded", initRealbookViewer);
