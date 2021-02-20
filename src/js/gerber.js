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
                <input
                    type='text'
                    class="standard-text-input"
                    id="dark-material"
                    placeholder="{ json material dict }"/>
            </div>
            <div>
                <label>Dark thickness</label>
                <input
                    type='text'
                    class="standard-text-input"
                    id="dark-thickness"
                    placeholder="units of length"/>
            </div>
            <div>
                <label>Clear material</label>
                <input
                    type='text'
                    class="standard-text-input"
                    id="clear-material"
                    placeholder="{ json material dict }"/>
            </div>
            <div>
                <label>Clear thickness</label>
                <input
                    type='text'
                    class="standard-text-input"
                    id="clear-thickness"
                    placeholder="units of length"/>
            </div>
            <div>
                <label>Region material</label>
                <input
                    type='text'
                    class="standard-text-input"
                    id="region-material"
                    placeholder="{ json material dict }"/>
            </div>
            <div>
                <label>Clear thickness</label>
                <input
                    type='text'
                    class="standard-text-input"
                    id="region-thickness"
                    placeholder="units of length"/>
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
    let $selectInput = $thisLayer.find(".gerber-layer-main select");
    $selectInput.on("input", showCustom);
    if (typeof layer_type == "string") {
        $selectInput.val(layer_type);
    }
    $selectInput.trigger("input");
}
function pushUserLayer(layer, $list) {
    $list.siblings(".gerber-add-layer").trigger("click", layer.mode);
    let $last = $list.find(".gerber-layer-box").last();
    $last
        .find(".gerber-layer-main input.standard-text-input")
        .val(layer.path);
    if (layer.mode == "CUSTOM") {
        let $custom = $last.find(".layer-custom-settings");
        $custom
            .find("#dark-material")
            .val(JSON.stringify(layer.data.dark_material));
        $custom
            .find("#dark-thickness")
            .val(layer.data.dark_thickness);
        $custom
            .find("#clear-material")
            .val(JSON.stringify(layer.data.clear_material));
        $custom
            .find("#clear-thickness")
            .val(layer.data.clear_thickness);
        $custom
            .find("#region-material")
            .val(JSON.stringify(layer.data.region_material));
        $custom
            .find("#region-thickness")
            .val(layer.data.region_thickness);
    }
}
function pullCustomMaterial($this, index, trace_name) {
    let raw_data;
    let data;
    try {
        raw_data = $this.val();
        data = JSON.parse(raw_data);
    } catch (e) {
        throw Error(
            `Unable to parse JSON data in layer ${index + 1}
custom material input no. 1. Expected JSON got '${raw_data}'.
`
        );
    }
    if (typeof data != "object")
        throw Error(`Invalid data type provided for ${trace_name} of layer ${
            index + 1
        }. Expected object, got ${typeof data}.
`);
    return data;
}
function pullCustomThickness($this, index, trace_name) {
    let raw_data = $this.val();
    if (isNaN(pF.parseUnitOfLength(raw_data)))
        throw Error(`Invalid data type provided for ${trace_name} of layer ${
            index + 1
        }. Expected object, got ${typeof raw_data}.
`);
    return raw_data;
}
function pullLayerConfig($this, index) {
    let out = {
        mode: "",
        path: "",
        data: {},
    };
    let path = $this.find("input.standard-text-input").val();
    if (!fs.existsSync(path)) {
        throw Error(
            `File path provided for layer ${
                index + 1
            } doesn't lead to an existing file`
        );
    } else {
        out.path = path;
    }
    out.mode = $this.find("select.standard-text-input").val();
    if (out.mode == "CUSTOM") {
        out.data.dark_material = pullCustomMaterial(
            $this.find("#dark-material"),
            index,
            "Dark material"
        );
        out.data.dark_thickness = pullCustomThickness(
            $this.find("#dark-thickness"),
            index,
            "Dark thickness"
        );
        out.data.clear_material = pullCustomMaterial(
            $this.find("#clear-material"),
            index,
            "Clear material"
        );
        out.data.clear_thickness = pullCustomThickness(
            $this.find("#clear-thickness"),
            index,
            "Clear thickness"
        );
        out.data.region_material = pullCustomMaterial(
            $this.find("#region-material"),
            index,
            "Region material"
        );
        out.data.region_thickness = pullCustomThickness(
            $this.find("#region-thickness"),
            index,
            "Region thickness"
        );
    }
    return out;
}
function pullGerbereConfig() {
    let out = {
        format: "LAYER_DATA",
        top_layers: [],
        bot_layers: [],
    };
    $("#gerber-layers-top")
        .find(".gerber-layer-box")
        .each(function (index) {
            out.top_layers.push(pullLayerConfig($(this), index));
        });
    $("#gerber-layers-bot")
        .find(".gerber-layer-box")
        .each(function (index) {
            out.bot_layers.push(pullLayerConfig($(this), index));
        });
    if (out.top_layers.length == 0 && out.top_layers.length == 0) {
        throw Error("Both layer lists are empty.");
    }
    return out;
}
function generateGerberModel() {
    try {
        let layers = pullGerbereConfig();
        let intervalID = null;
        let counter = 0;
        let f = function () {
            if (counter == 100) {
                console.log(counter);
            } else {
                $("#gerber-progress").val($("#gerber-progress").val() + 0.01);
                counter += 1;
                setTimeout(f, 50);
            }
        };
        setTimeout(f, 50);
    } catch (e) {
        dialog.showErrorBox("Unable to generate gerber model.", e.message);
        return;
    }
}
function saveGerberLayers() {
    try {
        let layers = pullGerbereConfig();
        let file = dialog.showSaveDialogSync({
            title: "Save gerber layer configuration to file",
            properties: [],
            filters: [
                { name: "JSON", extensions: ["json"] },
                { name: "Any", extensions: ["*"] },
            ],
        });
        if (file != undefined) {
            fs.writeFileSync(file, JSON.stringify(layers));
        }
    } catch (e) {
        dialog.showErrorBox("Unable to save gerber layers.", e.message);
        return;
    }
}
function loadGerberLayers() {
    let file = dialog.showOpenDialogSync({
        title: "Select JSOn file to load",
        properties: ["openFile"],
        filters: [
            { name: "JSON", extensions: ["json"] },
            { name: "Any", extensions: ["*"] },
        ],
    });
    let layer_data;
    if (file != undefined) {
        try {
            layer_data = JSON.parse(fs.readFileSync(file[0]));
        } catch (e) {
            throw Error(
                `Unable to parse selected file JSON error:\n${e.message}`
            );
        }
    } else {
        return;
    }
    if (layer_data.format != "LAYER_DATA") {
        throw Error(`Selected file is in incorrect format.`);
    } else {
        let $top = $("#gerber-layers-top");
        $top.empty();
        for (let layer of layer_data.top_layers) {
            pushUserLayer(layer, $top);
        }
        let $bot = $("#gerber-layers-bot");
        $bot.empty();
        for (let layer of layer_data.bot_layers) {
            pushUserLayer(layer, $bot);
        }
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
    $("#generate-gerber").on("click", generateGerberModel);
    $("#save-gerber-layers").on("click", saveGerberLayers);
    $("#load-gerber-layers").on("click", loadGerberLayers);
    let $sortableElement = $(".gerber-layer-list");
    $sortableElement.sortable();
    $sortableElement.sortable("option", "containment", "parent");
}
$(gerberUI);
