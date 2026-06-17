function toggleMenu(index)
{
    const menu =
        document.getElementById(
            "submenu-" + index
        );

    if(menu.style.display === "block")
    {
        menu.style.display = "none";
    }
    else
    {
        menu.style.display = "block";
    }
}

let mobileSelectedGroup = null;

function toggleMobileGroup(index) {

    const container =
        document.getElementById("mobileNavContent");

    if (mobileSelectedGroup === index) {

        mobileSelectedGroup = null;

        renderMobileRoot();

        return;
    }

    mobileSelectedGroup = index;

    renderMobileGroup(index);
}

function renderMobileRoot() {

    const container =
        document.getElementById("mobileNavContent");

    container.innerHTML = "";

    NAVIGATION_DATA.forEach((group, index) => {

        const btn =
            document.createElement("button");

        btn.className = "mobile-root-btn";

        btn.innerText = group.icon;

        btn.onclick =
            () => toggleMobileGroup(index);

        container.appendChild(btn);

    });
}

function renderMobileGroup(index) {

    const container =
        document.getElementById("mobileNavContent");

    container.innerHTML = "";

    const group =
        NAVIGATION_DATA[index];

    const rootBtn =
        document.createElement("button");

    rootBtn.className =
        "mobile-root-btn";

    rootBtn.innerText =
        group.icon;

    rootBtn.onclick =
        () => toggleMobileGroup(index);

    container.appendChild(rootBtn);

    group.items.forEach(item => {

        const link =
            document.createElement("a");

        link.className =
            "mobile-item-btn";

        link.href =
            item.url;

        link.innerText =
            item.icon;

        container.appendChild(link);

    });
}
const NAVIGATION_DATA =
    JSON.parse(
        document
            .getElementById("navigation-data")
            .textContent
    );

window.addEventListener(
    "DOMContentLoaded",
    renderMobileRoot
);

