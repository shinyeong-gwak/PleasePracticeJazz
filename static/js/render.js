let selected = null;

document.addEventListener("DOMContentLoaded", () => {
    loadScores();
});

async function loadScores() {
    const res = await fetch("/score-list");
    const files = await res.json();

    const list = document.getElementById("scoreList");
    list.innerHTML = "";

    files.forEach(file => {
        const item = document.createElement("div");
        item.className = "score-item";
        item.textContent = file.replace(/\.musicxml$/i, "");

        item.onclick = async () => {
            setActive(item);
            await render(file);
        };

        list.appendChild(item);
    });
}

function setActive(item) {
    if (selected)
        selected.classList.remove("active");

    item.classList.add("active");
    selected = item;
}

async function render(filename) {
    const res = await fetch("/render", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ filename })
    });

    document.getElementById("output").innerHTML = await res.text();
}