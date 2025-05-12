/** @odoo-module **/

console.log("✅ JS del portal cargado correctamente");

window.addEventListener("load", function () {
    console.log("📦 Página completamente cargada, inicializando listeners...");

    const teamSelect = document.getElementById("team");
    const parentSelect = document.getElementById("category_parent");
    const childSelect = document.getElementById("category");

    console.log("➡️ teamSelect:", teamSelect);
    console.log("➡️ parentSelect:", parentSelect);
    console.log("➡️ childSelect:", childSelect);

    if (teamSelect) {
        teamSelect.addEventListener("change", function () {
            console.log("🔁 Cambio de equipo detectado:", this.value);
            const teamId = this.value;
            const url = new URL(window.location.href);
            url.searchParams.set("team", teamId);
            window.location.href = url.toString();
        });
    }

    function filterSubcategories() {
        const parentId = parentSelect.value;
        console.log("🎯 Filtrando subcategorías para parentId:", parentId);
        Array.from(childSelect.options).forEach(opt => {
            const show = opt.dataset.parent === parentId;
            opt.hidden = !show && opt.value !== "";
        });
        childSelect.value = "";
    }

    if (parentSelect && childSelect) {
        filterSubcategories();
        parentSelect.addEventListener("change", filterSubcategories);
    }
});
