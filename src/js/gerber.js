const { type } = require("jquery");

function removeGerberLayer() {
    $(this).parents(".gerber-layer-box").remove();
}
function gerberFileSelect() {
    let file = dialog.showOpenDialogSync({
        title: "Select Gerber file",
        properties: ["openFile"],
        filters: [
            { name: "Gerber", extensions: ["grb", "gbr"] },
            { name: "Any", extensions: ["*"] },
        ],
    });
    if (file != undefined) {
        $(this).siblings("input").val(file);
    }
}
function showCustom() {
    if ($(this).val() == "CUSTOM") {
        $(this)
            .parents(".gerber-layer-box")
            .find(".layer-custom-settings")
            .show();
    } else {
        $(this)
            .parents(".gerber-layer-box")
            .find(".layer-custom-settings")
            .hide();
    }
}
function addLayerLine(event, layer_type) {
    $(this).siblings(".gerber-layer-list").append(`
    <div class="gerber-layer-box">
        <div class="gerber-layer-main">
            <input type='text' class="standard-text-input" placeholder="path to *.grb file"/>
            <div class="div-button" id="file-select">Select</div>
            <select class="standard-text-input">
                <option value="COPPER">Copper</option>
                <option value="SILK">Silk</option>
                <option value="PASTE_MASK">
                    Paste Mask
                </option>
                <option value="SOLDER_MASK">
                    Solder Mask
                </option>
                <option value="CUSTOM">Custom</option>
            </select>
            <span class="gerber-layer-remove-icon">&#10006</span>
        </div>
        <div class="layer-custom-settings">
            <div>
                <label>Dark material</label>
                <input type='text' class="standard-text-input" placeholder="{material dict}">
            </div>
            <div>
                <label>Clear material</label>
                <input type='text' class="standard-text-input" placeholder="{material dict}">
            </div>
            <div>
                <label>Region material</label>
                <input type='text' class="standard-text-input" placeholder="{material dict}">
            </div>
        </div>
    </div>
    `);
    let $thisLayer = $(this)
        .siblings(".gerber-layer-list")
        .children(".gerber-layer-box")
        .last();

    $thisLayer
        .find(".gerber-layer-main .gerber-layer-remove-icon")
        .on("click", removeGerberLayer);
    $thisLayer
        .find(".gerber-layer-main #file-select")
        .on("click", gerberFileSelect);
    let $sortableElement = $(this).siblings(".gerber-layer-list");
    $sortableElement.sortable();
    $sortableElement.sortable("option", "containment", "parent");
    let $selectInput = $thisLayer.find(".gerber-layer-main select");
    $selectInput.on("input", showCustom);
    if (typeof layer_type == "string") {
        $selectInput.val(layer_type);
    }
}
function gerberUI() {
    $(".gerber-add-layer").each(function () {
        $this = $(this);
        $this.on("click", addLayerLine);
        $this.trigger("click", "COPPER");
        $this.trigger("click", "PASTE_MASK");
        $this.trigger("click", "SOLDER_MASK");
        $this.trigger("click", "SILK");
    });
}
$(gerberUI);
