const { BlenderIO, IO_OUT, IO_IN } = require("../js/blenderio");

function removeGerberLayer() {
    $(this).parents(".gerber-layer-row").remove();
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
            .parents(".gerber-layer-row")
            .find(".gerber-layer-row-custom")
            .show();
    } else {
        $(this)
            .parents(".gerber-layer-row")
            .find(".gerber-layer-row-custom")
            .hide();
    }
}
function addLayerLine(event, layer_type) {
    $(this).siblings(".gerber-layer-list").append(`
    <div class="gerber-layer-row">
        <div class="gerber-layer-row-main">
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
        <div class="gerber-layer-row-custom">
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
        .children(".gerber-layer-row")
        .last();

    $thisLayer
        .find(".gerber-layer-row-main .gerber-layer-remove-icon")
        .on("click", removeGerberLayer);
    $thisLayer
        .find(".gerber-layer-row-main #file-select")
        .on("click", gerberFileSelect);
    let $selectInput = $thisLayer.find(".gerber-layer-row-main select");
    $selectInput.on("input", showCustom);
    if (typeof layer_type == "string") {
        $selectInput.val(layer_type);
    }
    $selectInput.trigger("input");
}
function pushUserLayer(layer, $list) {
    $list.siblings(".gerber-add-layer").trigger("click", layer.mode);
    let $last = $list.find(".gerber-layer-row").last();
    $last
        .find(".gerber-layer-row-main input.standard-text-input")
        .val(layer.path);
    if (layer.mode == "CUSTOM") {
        let $custom = $last.find(".gerber-layer-row-custom");
        $custom
            .find("#dark-material")
            .val(JSON.stringify(layer.data.dark_material));
        $custom.find("#dark-thickness").val(layer.data.dark_thickness);
        $custom
            .find("#clear-material")
            .val(JSON.stringify(layer.data.clear_material));
        $custom.find("#clear-thickness").val(layer.data.clear_thickness);
        $custom
            .find("#region-material")
            .val(JSON.stringify(layer.data.region_material));
        $custom.find("#region-thickness").val(layer.data.region_thickness);
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
        .find(".gerber-layer-row")
        .each(function (index) {
            out.top_layers.push(pullLayerConfig($(this), index));
        });
    $("#gerber-layers-bot")
        .find(".gerber-layer-row")
        .each(function (index) {
            out.bot_layers.push(pullLayerConfig($(this), index));
        });
    if (out.top_layers.length == 0 && out.top_layers.length == 0) {
        throw Error("Both layer lists are empty.");
    }
    return out;
}
function setGerberProgress(value, max) {
    if (max != 0 && value != 0) {
        let prct = (value / max) * 100;
        $("#gerber-progress").css("width", `${prct}%`);
        $("#gerber-progress-label").text(`${value}/${max}`);
    } else if (max == 0 && value != 0) {
        $("#gerber-progress").css("width", `0%`);
        $("#gerber-progress-label").text(`Interrupted`);
    } else {
        $("#gerber-progress").css("width", `0%`);
        $("#gerber-progress-label").text(`0/0`);
    }
}
let TOKEN_STACK_SIZE = 0;
let TOKENS_DONE = 0;
let STOP_GERBER_GENERATION = false;
let GENERATION_LOCK = false;
let RENDERING_LOCK = false;
let PREVIEW_PATH = null;
async function generateGerberLayer(layer, layer_type, layer_id) {
    STOP_GERBER_GENERATION = false;
    let blender_io = new BlenderIO(userpref);
    await blender_io.begin();
    try {
        let mess = await blender_io.call(
            new IO_OUT("renderGerberLayer", {
                layer_type: layer_type,
                layer: layer,
                layer_id: layer_id,
            }),
            "STREAM"
        );
        TOKEN_STACK_SIZE += mess.data.token_count;
        while (true) {
            mess = await blender_io.read();
            if (mess.status == "END") {
                break;
            } else if (mess.status == "STREAM") {
                TOKENS_DONE += mess.data.tokens_done;
                if (STOP_GERBER_GENERATION) {
                    blender_io.write(new IO_OUT("STOP"));
                    TOKENS_DONE = 1;
                    TOKEN_STACK_SIZE = 0;
                    setGerberProgress(1, 0);
                    throw Error("GENINT");
                } else {
                    blender_io.write(new IO_OUT("CONTINUE"));
                }
            } else if (mess.status == "ERROR") {
                throw Error(mess.data.trace);
            }
        }
    } finally {
        blender_io.kill();
    }
}
async function joinGerberLayers(top_layers, bot_layers) {
    let blender_io = new BlenderIO(userpref);
    await blender_io.begin();
    try {
        await blender_io.call(
            new IO_OUT("joinLayers", {
                top_layers: top_layers,
                bot_layers: bot_layers,
            }),
            "OK"
        );
    } finally {
        blender_io.kill();
    }
}
function clearGerberCache() {
    TOKENS_DONE = 0;
    TOKEN_STACK_SIZE = 0;
    setGerberProgress(TOKENS_DONE, TOKEN_STACK_SIZE);
    if (!fs.existsSync("./temp")) {
        fs.mkdirSync("./temp");
    }
    if (fs.existsSync("./temp/gerber")) {
        fs.rmdirSync("./temp/gerber", { recursive: true });
    }
    fs.mkdirSync("./temp/gerber");

    $("#gerber-preview").prop(
        "src",
        `${process.cwd()}\\data\\assets\\img\\img-broken.svg`
    );
}
async function generateGerberModel() {
    if (!GENERATION_LOCK) {
        GENERATION_LOCK = true;
        clearGerberCache();
        let progressID = setInterval(
            () => setGerberProgress(TOKENS_DONE, TOKEN_STACK_SIZE),
            100
        );
        let layers;
        try {
            layers = pullGerbereConfig();
        } catch (e) {
            layers = undefined;
            showErrorBox("Unable to pull gerber layer confguration.", e);
        }
        if (layers != undefined) {
            let promises = [];
            let _index = 0;
            let top_layers = [];
            let bot_layers = [];
            for (let layer of layers.top_layers) {
                promises.push(generateGerberLayer(layer, "TOP", _index));
                top_layers.push(
                    `${process.cwd()}/temp/gerber/gerber-${_index}.glb`
                );
                _index += 1;
            }
            for (let layer of layers.bot_layers) {
                promises.push(generateGerberLayer(layer, "BOT", _index));
                bot_layers.push(
                    `${process.cwd()}/temp/gerber/gerber-${_index}.glb`
                );
                _index += 1;
            }
            let interrupt = false;
            for (let p of promises) {
                try {
                    await p;
                } catch (e) {
                    interrupt = true;
                    if (e.message != "GENINT")
                        showErrorBox(
                            "Unable to continue generation due to fatal error.",
                            e
                        );
                }
            }
            clearInterval(progressID);
            if (!interrupt) {
                try {
                    TOKENS_DONE = TOKEN_STACK_SIZE;
                    setGerberProgress(TOKENS_DONE, TOKEN_STACK_SIZE);
                    await joinGerberLayers(top_layers, bot_layers);
                    dialog.showMessageBox({
                        type: "info",
                        buttons: ["Ok"],
                        title: "Finished generating 3D model files.",
                        message: `Tokens resolved: ${TOKEN_STACK_SIZE}. Now you can render preview.`,
                    });
                } catch (e) {
                    showErrorBox(
                        "Unable to finish model processing due to fatal error.",
                        e
                    );
                }
            }
        }
        GENERATION_LOCK = false;
    }
}
function interruptModelGeneration() {
    if (GENERATION_LOCK && !RENDERING_LOCK) {
        STOP_GERBER_GENERATION = true;
    } else {
        dialog.showErrorBox(
            "Nothing to interrupt.",
            "No generation process is currently running."
        );
    }
}
function saveGerberModel() {
    if (!GENERATION_LOCK && TOKENS_DONE != 0) {
        let save_as_path = dialog.showSaveDialogSync({
            title: "Save 3D model",
            properties: [],
            filters: [{ name: "glTF 2.0", extensions: ["glb"] }],
        });
        if (save_as_path != undefined) {
            fs.copyFileSync("./temp/gerber/merged.glb", save_as_path);
        }
    } else {
        dialog.showErrorBox(
            "Unable to save model.",
            "You haven't generated gerber model."
        );
    }
}
async function renderPreview() {
    if (!GENERATION_LOCK && TOKENS_DONE != 0) {
        GENERATION_LOCK = true;
        RENDERING_LOCK = true;
        $("#render-gerber").addClass("breath-div-button");
        try {
            let render_file = new Date().getTime().toString();
            let blender_io = new BlenderIO(userpref);
            await blender_io.begin();
            try {
                await blender_io.call(
                    new IO_OUT("renderPreview", {
                        source: `${process.cwd()}/temp/gerber/merged.glb`,
                        render_file: `${process.cwd()}/temp/gerber/${render_file}.png`,
                    }),
                    "OK"
                );
            } finally {
                blender_io.kill();
            }
            let preview = $("#gerber-preview");
            PREVIEW_PATH = `${process.cwd()}/temp/gerber/${render_file}.png`;
            preview.prop("src", PREVIEW_PATH);
            preview.css({ top: 0, left: 0 });
        } catch (e) {
            showErrorBox("Unable to finish rendering.", e);
        }
        $("#render-gerber").removeClass("breath-div-button");
        GENERATION_LOCK = false;
        RENDERING_LOCK = false;
    } else if (!GENERATION_LOCK) {
        dialog.showErrorBox(
            "Unable to start rendering process",
            "You can only generate/render one file at once."
        );
    } else {
        dialog.showErrorBox(
            "Unable to start rendering process",
            "You have to generate 3D model before you can render it."
        );
    }
}
function savePreview() {
    if (PREVIEW_PATH != null) {
        let save_as_path = dialog.showSaveDialogSync({
            title: "Save 3D model",
            properties: [],
            filters: [{ name: "PNG image", extensions: ["png"] }],
        });
        if (save_as_path != undefined) {
            fs.copyFileSync(PREVIEW_PATH, save_as_path);
        }
    } else {
        dialog.showErrorBox(
            "No preview available.",
            "You haven't generated any gerber file preview."
        );
    }
}
function recognizeFilesFromDir() {
    let dir;
    try {
        dir = dialog.showOpenDialogSync({
            title: "Directory to recognize files from.",
            properties: ["openDirectory"],
        })[0];
    } catch (e) {
        dir = undefined;
    }
    if (dir != undefined) {
        let top_layers = {
            ".*?top.*?copper.*?\\.g[rb][rb]": null,
            ".*?top.*?paste.*?\\.g[rb][rb]": null,
            ".*?top.*?solder.*?\\.g[rb][rb]": null,
            ".*?top.*?silk.*?\\.g[rb][rb]": null,
        };
        let bot_layers = {
            ".*?bot.*?copper.*?\\.g[rb][rb]": null,
            ".*?bot.*?paste.*?\\.g[rb][rb]": null,
            ".*?bot.*?solder.*?\\.g[rb][rb]": null,
            ".*?bot.*?silk.*?\\.g[rb][rb]": null,
        };
        for (let file of fs.readdirSync(dir)) {
            try {
                for (let regex in top_layers) {
                    if (file.match(regex) != null) {
                        top_layers[regex] = `${dir}\\${file}`;
                        throw Error();
                    }
                }
                for (let regex in bot_layers) {
                    if (file.match(regex) != null) {
                        bot_layers[regex] = `${dir}\\${file}`;
                        throw Error();
                    }
                }
            } catch (e) {}
        }
        let layer_data = { top_layers: [], bot_layers: [] };
        let appendLayer = function (__layers, _regex, _layer, _mode) {
            if (__layers[_regex] != null) {
                layer_data[_layer].push({
                    mode: _mode,
                    path: __layers[_regex],
                    data: {},
                });
            }
        };
        // top layers
        appendLayer(
            top_layers,
            ".*?top.*?copper.*?\\.g[rb][rb]",
            "top_layers",
            "COPPER"
        );
        appendLayer(
            top_layers,
            ".*?top.*?solder.*?\\.g[rb][rb]",
            "top_layers",
            "SOLDER_MASK"
        );
        appendLayer(
            top_layers,
            ".*?top.*?paste.*?\\.g[rb][rb]",
            "top_layers",
            "PASTE_MASK"
        );
        appendLayer(
            top_layers,
            ".*?top.*?silk.*?\\.g[rb][rb]",
            "top_layers",
            "SILK"
        );
        // bottom layers
        appendLayer(
            bot_layers,
            ".*?bot.*?copper.*?\\.g[rb][rb]",
            "bot_layers",
            "COPPER"
        );
        appendLayer(
            bot_layers,
            ".*?bot.*?solder.*?\\.g[rb][rb]",
            "bot_layers",
            "SOLDER_MASK"
        );
        appendLayer(
            bot_layers,
            ".*?bot.*?paste.*?\\.g[rb][rb]",
            "bot_layers",
            "PASTE_MASK"
        );
        appendLayer(
            bot_layers,
            ".*?bot.*?silk.*?\\.g[rb][rb]",
            "bot_layers",
            "SILK"
        );
        loadLayersToGUI(layer_data);
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
        showErrorBox("Unable to save gerber layers.", e);
        return;
    }
}
function loadLayersToGUI(layer_data) {
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
function loadGerberLayers() {
    let file = dialog.showOpenDialogSync({
        title: "Select JSON file to load",
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
        loadLayersToGUI(layer_data);
    }
}
let GERBER_PREVIEW_SCALE = 1;
function zoomGerberPreview(event) {
    if (event.code == "Equal" && event.ctrlKey) {
        GERBER_PREVIEW_SCALE *= 1.1;
        $("#gerber-preview").css({
            transform: `scale(${GERBER_PREVIEW_SCALE})`,
        });
    } else if (event.code == "Minus" && event.ctrlKey) {
        GERBER_PREVIEW_SCALE /= 1.1;
        $("#gerber-preview").css({
            transform: `scale(${GERBER_PREVIEW_SCALE})`,
        });
    }
}
function gerberUI() {
    $("#gerber-container").on("keydown", zoomGerberPreview);
    $("#gerber-container").on("mousewheel", event => {
        if (event.originalEvent.wheelDelta > 0) {
            zoomGerberPreview({ code: "Equal", ctrlKey: true });
        } else {
            zoomGerberPreview({ code: "Minus", ctrlKey: true });
        }
    });
    $("#gerber-preview").draggable();
    $(".gerber-add-layer").each(function () {
        $this = $(this);
        $this.on("click", addLayerLine);
        $this.trigger("click", "COPPER");
        $this.trigger("click", "PASTE_MASK");
        $this.trigger("click", "SOLDER_MASK");
        $this.trigger("click", "SILK");
    });
    $("#generate-gerber").on("click", generateGerberModel);
    $("#render-gerber").on("click", renderPreview);
    $("#stop-generate-gerber").on("click", interruptModelGeneration);
    $("#save-gerber-model").on("click", saveGerberModel);
    $("#save-gerber-preview").on("click", savePreview);
    $("#recoginze-gerber-dir").on("click", recognizeFilesFromDir);
    $("#save-gerber-layers").on("click", saveGerberLayers);
    $("#load-gerber-layers").on("click", loadGerberLayers);
    let $sortableElement = $(".gerber-layer-list");
    $sortableElement.sortable();
    $sortableElement.sortable("option", "containment", "parent");
}
$(gerberUI);
