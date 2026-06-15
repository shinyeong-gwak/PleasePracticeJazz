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