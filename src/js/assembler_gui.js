function addAssemblerComponent(signature, model, label, cox, coy, rot, top) {
    $("#assembler-components-list").append(
        `<div class="assembler-component-body">
            <div class="assembler-component-body-title" signature="${signature}"><div>&#x203A;</div>${signature} ${model}</div>
            <div class="assembler-component-body-inner">
                <div class="assembler-component-body-row">
                    <div>model</div>
                    <input class="standard-text-input" id="as-model" value="${model}" list="models-names" />
                    <div>label</div>
                    <input class="standard-text-input" id="as-label" value="${label}" />
                </div>
                <div class="assembler-component-body-row">
                    <div>co. X</div>
                    <input class="standard-text-input assembler-short" id="as-cox" value="${cox}" />
                    <div>co. Y</div>
                    <input class="standard-text-input assembler-short" id="as-coy" value="${coy}" />
                </div>
                <div class="assembler-component-body-row">
                    <div>Rot</div>
                    <input class="standard-text-input assembler-short" id="as-rot" value="${rot}" />
                    <div>Top</div>
                    <label class="switch">
                        <input type="checkbox" id="as-top" />
                        <span class="slider round"></span>
                    </label>
                </div>
            </div>
        </div>`
    );
    let $this = $("#assembler-components-list")
        .find(".assembler-component-body")
        .last();
    $this.find(".assembler-component-body-title").on("click", function () {
        $body = $(this).next();
        if ($body.is(":hidden")) {
            $body.show();
            $(this).find("div").css({ transform: "rotate(90deg)" });
        } else {
            $body.hide();
            $(this).find("div").css({ transform: "rotate(0deg)" });
        }
    });
    $this.find(".switch input").attr("checked", top);
    $this.find(".assembler-component-body-title").trigger("click");
}
let previewPCB_ID = null;
async function showAssemblerPreview() {
    if (disableComponent(this)) {
        let pcb_model = $("#assembler-pcb-src").val();
        let hashCode = pcb_model.hashCode();
        if (pcb_model.length == 0 || !fs.existsSync(pcb_model)) {
            return;
        } else if (hashCode != previewPCB_ID) {
            try {
                let blender_io = new BlenderIO(userpref);
                await blender_io.begin();
                try {
                    await blender_io.call(
                        new IO_OUT("renderPreview", {
                            source: pcb_model,
                            render_file: `${process.cwd()}/temp/assembler/${hashCode}.png`,
                        }),
                        "OK"
                    );
                    previewPCB_ID = hashCode;
                } finally {
                    blender_io.kill();
                }
            } catch (e) {
                showErrorBox("Unable render PCB preview.", e);
                clearTimeout(REFRESH_ASSEMBLER_PREVIEW_ID);
            }
        }
        let $box = $("#assemble-preview-panel").find(".assembler-preview-box");
        $box.empty();
        $box.append(
            `<img src="${process.cwd()}/temp/assembler/${previewPCB_ID}.png" />`
        );
        enableComponent(this);
    }
}
function buildComponentsList(dict) {
    let keys = Object.keys(dict)
        .sort()
        .reduce((obj, key) => {
            obj[key] = dict[key];
            return obj;
        }, {});
    for (let key in keys) {
        addAssemblerComponent(
            key,
            dict[key].model,
            dict[key].label,
            dict[key].cox,
            dict[key].coy,
            dict[key].rot,
            dict[key].top
        );
    }
}
function pullComponentSetup() {
    let setup = {};
    $("#assembler-components-list")
        .find(".assembler-component-body")
        .each(function () {
            let $this = $(this);
            let key = $this
                .find(".assembler-component-body-title")
                .attr("signature");
            let model = $this.find("#as-model").val();
            if (models[model] == undefined) {
                throw Error(
                    `Model: "${model}" used for component '${key}' not found in library.`
                );
            }
            setup[key] = {
                model: model,
                label: $this.find("#as-label").val(),
                cox: $this.find("#as-cox").val(),
                coy: $this.find("#as-coy").val(),
                rot: $this.find("#as-rot").val(),
                top: $this.find("#as-top").attr("checked"),
            };
        });
    return setup;
}
let EXISTING_COMPONENTS = {};
async function prebuildComponents() {
    let setup = pullComponentSetup();
    if (!fs.existsSync("./temp/assembler")) {
        EXISTING_COMPONENTS = {};
        fs.mkdirSync("./temp/assembler", { recursive: true });
    }
    if (setup == undefined) {
        throw Error("No components to mount.");
    }
    let blender_setup = {};
    let _prom = [];
    for (let key in setup) {
        let reload = false;
        let model = models[setup[key].model];
        let params = model.traverse();
        params.label = setup[key].label;
        let model_path;
        if (
            EXISTING_COMPONENTS[key] == undefined ||
            EXISTING_COMPONENTS[key].params != params
        ) {
            reload = true;
            model_path = `./temp/assembler/${Date.now()}.glb`;
            _prom.push(model.make(params, model_path));
            EXISTING_COMPONENTS[key] = {
                path: model_path,
                params: params,
            };
        }
        blender_setup[key] = {
            path: EXISTING_COMPONENTS[key].path,
            reload: reload,
            cox: parseFloat(setup[key].cox),
            coy: parseFloat(setup[key].coy),
            rot: parseFloat(setup[key].rot),
            top: setup[key].top,
        };
    }
    for (let key in EXISTING_COMPONENTS) {
        if (setup[key] == undefined) {
            fs.unlinkSync(EXISTING_COMPONENTS.path);
            delete EXISTING_COMPONENTS[key];
        }
    }
    for (let p of _prom) {
        await p;
    }
    return blender_setup;
}
let ASSEMBLER_PROJECT_NAME = "";
let ASSEMBLER_PARTSLIST_COMPONENTS_LIST = {};
let ASSEMBLER_PLACE_POSITION_LIST = {};
const loadComponents = {
    JSON: function (path) {
        try {
            buildComponentsList(JSON.parse(fs.readFileSync(path).toString()));
        } catch (e) {
            showErrorBox("Unable to load json file.", e);
        }
    },
    PARTSLIST: function (path) {
        try {
            ASSEMBLER_PARTSLIST_COMPONENTS_LIST = {};
            let source = fs.readFileSync(path).toString();
            source = source.replace(/====\+.*?\+====\s*/, "").trim();
            for (let line of source.split("\n")) {
                let [marks, _, ...dscp] = line.split(/\s+/);
                dscp = dscp.join("");
                marks = marks.split(",");
                let [label, ___, model] = dscp.split(",");
                for (let mark of marks) {
                    ASSEMBLER_PARTSLIST_COMPONENTS_LIST[mark] = {
                        model: model,
                        label: label,
                    };
                }
            }
            if (
                !$.isEmptyObject(ASSEMBLER_PARTSLIST_COMPONENTS_LIST) &&
                !$.isEmptyObject(ASSEMBLER_PLACE_POSITION_LIST)
            ) {
                buildComponentsList(this._MERGE_PARTSLIST_PLACE());
            }
        } catch (e) {
            showErrorBox("Unable to load parts list file.", e);
        }
    },
    PLACE: function (path) {
        try {
            let source = fs.readFileSync(path).toString();
            ASSEMBLER_PLACE_POSITION_LIST = {};
            ASSEMBLER_PROJECT_NAME = source.match(/(?:Project:)\s*(.*)\s+/)[1];
            let units = source.match(/(?:Units:)\s*(.*)\s+/)[1];
            let multiplier = 1;
            // convert to cm
            switch (units) {
                case "INCH":
                    multiplier = 2.54;
                    break;

                default:
                    break;
            }
            source = source.replace(/.*?----------  ----\s+/s, "").trim();
            for (let line of source.split("\n")) {
                let [
                    mark,
                    model,
                    side,
                    cox,
                    coy,
                    rot,
                    glux,
                    gluy,
                    gludia,
                    tech,
                    pins,
                ] = line.split(/\s+/);
                ASSEMBLER_PLACE_POSITION_LIST[mark] = {
                    cox: cox * multiplier,
                    coy: coy * multiplier,
                    rot: rot,
                    top: side == "Top",
                };
            }

            if (
                !$.isEmptyObject(ASSEMBLER_PARTSLIST_COMPONENTS_LIST) &&
                !$.isEmptyObject(ASSEMBLER_PLACE_POSITION_LIST)
            ) {
                buildComponentsList(this._MERGE_PARTSLIST_PLACE());
            }
        } catch (e) {
            showErrorBox("Unable to load place file.", e);
        }
    },
    _MERGE_PARTSLIST_PLACE() {
        let component_list = {};
        for (let key in ASSEMBLER_PARTSLIST_COMPONENTS_LIST) {
            component_list[key] = {
                model: ASSEMBLER_PARTSLIST_COMPONENTS_LIST[key].model,
                label: ASSEMBLER_PARTSLIST_COMPONENTS_LIST[key].label,
                top: ASSEMBLER_PLACE_POSITION_LIST[key].top,
                cox: ASSEMBLER_PLACE_POSITION_LIST[key].cox,
                coy: ASSEMBLER_PLACE_POSITION_LIST[key].coy,
                rot: ASSEMBLER_PLACE_POSITION_LIST[key].rot,
            };
        }
        return component_list;
    },
};
let ASSEMBLER_PREVIEW_SCALE = 1;
function zoomAssemblerPreview(event) {
    if (event.code == "Equal" && event.ctrlKey) {
        ASSEMBLER_PREVIEW_SCALE *= 1.1;
        $("#assemble-preview-panel")
            .find(".assembler-preview-box")
            .css({
                transform: `scale(${ASSEMBLER_PREVIEW_SCALE})`,
            });
    } else if (event.code == "Minus" && event.ctrlKey) {
        ASSEMBLER_PREVIEW_SCALE /= 1.1;
        $("#assemble-preview-panel")
            .find(".assembler-preview-box")
            .css({
                transform: `scale(${ASSEMBLER_PREVIEW_SCALE})`,
            });
    }
}
$(async function () {
    $("#assemble-preview-panel").on("keydown", zoomGerberPreview);
    $("#assemble-preview-panel").on("mousewheel", event => {
        if (event.ctrlKey) {
            if (event.originalEvent.wheelDelta > 0) {
                zoomAssemblerPreview({ code: "Equal", ctrlKey: true });
            } else {
                zoomAssemblerPreview({ code: "Minus", ctrlKey: true });
            }
        }
    });
    $("#assemble-preview-panel").find(".assembler-preview-box").draggable();
    $("#assembler-comp-src-type-select").on("click", function () {
        $(".assembler-comp-src").hide();
        $(`#${$(this).val()}`).show();
    });
    $(".assembler-comp-src").hide();
    $("#assembler-comp-src-type-select").trigger("click");
    $(".assembler-subsection-header").on("click", function () {
        let $this = $(this);
        let $body = $this.next();
        if ($body.is(":hidden")) {
            $body.show();
            $this.find("div").css({ transform: "rotate(90deg)" });
        } else {
            $body.hide();
            $this.find("div").css({ transform: "rotate(0deg)" });
        }
    });
    $(`.assembler-comp-src input`).on("click", function () {
        let $this = $(this);
        let filters = [];
        for (let pair of $this.attr("ext").split(";")) {
            let pair_split = pair.split(":");
            filters.push({ name: pair_split[0], extensions: [pair_split[1]] });
        }
        let file = dialog.showOpenDialogSync({
            title: `Open ${$this.prev().text().trim()} file`,
            properties: ["openFile"],
            filters: filters,
        });
        if (file != undefined) {
            $this.val(file);
            switch ($this.prev().text().trim()) {
                case "Parts list":
                    loadComponents.PARTSLIST(file[0]);
                    break;
                case "Place":
                    loadComponents.PLACE(file[0]);
                    break;
                case "JSON":
                    loadComponents.JSON(file[0]);
                    break;

                default:
                    break;
            }
        }
    });
    $("#assembler-pcb-src").on("click", function () {
        let $this = $(this);
        let filters = [];
        for (let pair of $this.attr("ext").split(";")) {
            let pair_split = pair.split(":");
            filters.push({ name: pair_split[0], extensions: [pair_split[1]] });
        }
        let file = dialog.showOpenDialogSync({
            title: `Open ${$this.prev().text().trim()} file`,
            properties: ["openFile"],
            filters: filters,
        });
        if (file != undefined) {
            $this.val(file);
        }
    });
    $(".assembler-subsection-header").trigger("click");

    $("#assembler-controls :nth-child(1).div-button").on(
        "click",
        async function () {
            if (disableComponent(this)) {
                let blender_io = new BlenderIO(userpref);
                await blender_io.begin();
                try {
                    let pcb_model = $("#assembler-pcb-src").val();
                    if (pcb_model.length == 0) {
                        throw Error("No PCB model selected.");
                    } else if (!fs.existsSync(pcb_model)) {
                        throw Error("Selected file doesn't exist.");
                    }
                    let file = dialog.showSaveDialogSync({
                        title: "Save assembled 3D model",
                        properties: [],
                        filters: [{ name: "glTF 2.0", extensions: ["glb"] }],
                    });
                    if (file != undefined) {
                        let setup = await prebuildComponents();
                        try {
                            let resp = await blender_io.call(
                                new IO_OUT("buildAssembler", {
                                    pcb: pcb_model,
                                    setup: setup,
                                    out: file,
                                })
                            );
                        } finally {
                            blender_io.kill();
                        }
                    }
                } catch (e) {
                    showErrorBox("Unable to build 3D model.", e);
                }
                enableComponent(this);
            }
        }
    );
    $("#assembler-controls :nth-child(2).div-button").on("click", function () {
        try {
            let file = dialog.showSaveDialogSync({
                title: "Save assembler setup to file",
                properties: [],
                filters: [{ name: "Assembler Setup", extensions: ["astp"] }],
            });
            if (file != undefined) {
                fs.writeFileSync(file, JSON.stringify(pullComponentSetup()));
            }
        } catch (e) {
            showErrorBox("Unable to export setup.", e);
            return;
        }
    });
    $("#assembler-controls :nth-child(4).div-button").on(
        "click",
        showAssemblerPreview
    );
});
