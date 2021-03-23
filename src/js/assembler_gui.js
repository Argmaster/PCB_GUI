ASSEMBLER = {
    appendSetup: function (signature, model, footprint, cox, coy, rot, top) {
        ASSEMBLER.getSetupGUI().append(
            `<div class="assembler-component-body">
            <div class="assembler-component-body-title" signature="${signature}"><div>&#x203A;</div>${signature}</div>
            <div class="assembler-component-body-inner">
                <div class="assembler-component-body-row">
                    <div>model</div>
                    <input class="standard-text-input" id="as-model" value="${model}" list="models-names" />
                    <div>ftp.</div>
                    <input class="standard-text-input" id="as-footprint" value="${footprint}" />
                </div>
                <div class="assembler-component-body-row">
                    <div>co. X</div>
                    <input class="standard-text-input assembler-short" id="as-cox" value="${cox}" />
                    <div>co. Y</div>
                    <input class="standard-text-input assembler-short" id="as-coy" value="${coy}" />
                </div>
                <div class="assembler-component-body-row">
                    <div>Rot</div>
                    <input class="standard-text-input assembler-short" type="number" step="90" id="as-rot" value="${rot}" />
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
    },
    imageSize: function ($target) {
        return new Promise(resolve =>
            $target.on("load", function () {
                resolve([this.width, this.height]);
            })
        );
    },
    previewPCB_ID: null,
    _pcb_CO: null,
    renderPCB: async function () {
        let pcb_path = $("#assembler-pcb-src").val();
        let hashCode = pcb_path.hashCode();
        if (pcb_path.length == 0) {
            throw Error("No PCB model selected.");
        } else if (!fs.existsSync(pcb_path)) {
            throw Error("Selected path to PCB model doesn't exist.");
        }
        let pcb_img_path = `${process.cwd()}/temp/pcb${hashCode}.png`;
        if (hashCode != ASSEMBLER.previewPCB_ID) {
            if (ASSEMBLER.previewPCB_ID != null) {
                fs.unlinkSync(
                    `${process.cwd()}/temp/pcb${ASSEMBLER.previewPCB_ID}.png`
                );
            }
            let blender_io = new BlenderIO(userpref);
            await blender_io.begin();
            try {
                ASSEMBLER._pcb_CO = (
                    await blender_io.call(
                        new IO_OUT("renderPreview", {
                            source: pcb_path,
                            render_file: pcb_img_path,
                        }),
                        "DONE"
                    )
                ).data.co;

                ASSEMBLER.previewPCB_ID = hashCode;
            } finally {
                blender_io.kill();
            }
        }
        return pcb_img_path;
    },
    appendPreview: async function (key, cpos, $box) {
        $box.append(
            `<img src="${cpos.model_pkg}/__top__.png" class="component" >${key}</img>`
        );
        let $comp = $box.find(".component").last();
        let [x, y] = await ASSEMBLER.imageSize($comp);
        let dpm = userpref.get("debug.blender.dpi") * 40;
        let pcb_height = ASSEMBLER._pcb_CO.sy * dpm;

        $comp.draggable();
        let $gui = $(`[signature="${key}"]`).next();
        let $as_cox = $gui.find("#as-cox");
        let $as_coy = $gui.find("#as-coy");
        let $as_rot = $gui.find("#as-rot");

        $as_cox.on("input", () => {
            $comp.css({ left: `${($as_cox.val() / 100) * dpm - x / 2}px` });
        });
        $as_coy.on("input", () => {
            $comp.css({
                top: `${pcb_height - ($as_coy.val() / 100) * dpm - y / 2}px`,
            });
        });
        $as_rot.on("input", () => {
            $comp.css({
                transform: `rotateZ(-${$as_rot.val()}deg)`,
            });
        });

        $comp.on("drag", function (event, ui) {
            ui.position = {
                left: ui.position.left / ASSEMBLER.PREVIEW_SCALE,
                top: ui.position.top / ASSEMBLER.PREVIEW_SCALE,
            };
            ui.originalPosition = {
                left: ui.originalPosition.left / ASSEMBLER.PREVIEW_SCALE,
                top: ui.originalPosition.top / ASSEMBLER.PREVIEW_SCALE,
            };
            $comp.trigger("click");

            $as_cox.val(((ui.position.left + x / 2) / dpm) * 100);
            $as_coy.val(((pcb_height - (ui.position.top + y / 2)) / dpm) * 100);
        });
        $comp.on("click", function (event) {
            $("#assembler-components-list")
                .find(".assembler-component-body")
                .each(function () {
                    let $box = $(this).find(".assembler-component-body-inner");
                    if (!$box.is(":hidden")) {
                        $box.prev().trigger("click");
                    }
                });
            $gui.prev().trigger("click");
            if (event.ctrlKey) {
                $as_rot.val(
                    (Math.floor(parseFloat($as_rot.val()) / 45) * 45 + 45) % 360
                );
                $as_rot.trigger("input");
            }
        });
        $as_cox.trigger("input");
        $as_coy.trigger("input");
        $as_rot.trigger("input");
    },
    getPreview: function () {
        return $("#assemble-preview-panel").find(".assembler-preview-box");
    },
    clearPreview: function () {
        let $box = ASSEMBLER.getPreview();
        $box.empty();
        return $box;
    },
    showPreview: async function () {
        if (disableComponent(this)) {
            try {
                let setup = ASSEMBLER.getSetup();
                let pcb_img_path = await ASSEMBLER.renderPCB();
                let $box = ASSEMBLER.clearPreview();
                $box.append(`<img src="${pcb_img_path}" />`);
                let cpos = ASSEMBLER.toPosition(setup);
                for (let k in cpos) {
                    if (cpos[k].top) ASSEMBLER.appendPreview(k, cpos[k], $box);
                }
            } catch (e) {
                showErrorBox("Unable render PCB preview.", e);
            }
            enableComponent(this);
        }
    },
    getSetupGUI: function () {
        return $("#assembler-components-list");
    },
    clearSetupGUI: function () {
        ASSEMBLER.clearPreview();
        ASSEMBLER.getSetupGUI().empty();
    },
    loadSetupGUI: function (dict) {
        ASSEMBLER.clearSetupGUI();
        let keys = Object.keys(dict)
            .sort()
            .reduce((obj, key) => {
                obj[key] = dict[key];
                return obj;
            }, {});
        for (let key in keys) {
            ASSEMBLER.appendSetup(
                key,
                dict[key].model,
                dict[key].footprint,
                dict[key].cox,
                dict[key].coy,
                dict[key].rot,
                dict[key].top
            );
        }
    },
    getSetup: function () {
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
                    footprint: $this.find("#as-footprint").val(),
                    cox: $this.find("#as-cox").val(),
                    coy: $this.find("#as-coy").val(),
                    rot: $this.find("#as-rot").val(),
                    top: $this.find("#as-top").prop("checked"),
                };
            });
        return setup;
    },
    toPosition: function (setup) {
        let out = {};
        for (let key in setup) {
            out[key] = {
                model_pkg: models[setup[key].model].package_path,
                cox: parseFloat(setup[key].cox) / 100,
                coy: parseFloat(setup[key].coy) / 100,
                rot: parseFloat(setup[key].rot),
                top: setup[key].top,
            };
        }
        return out;
    },
    loadFile: {
        JSON: function (path) {
            try {
                ASSEMBLER.loadSetupGUI(
                    JSON.parse(fs.readFileSync(path).toString())
                );
            } catch (e) {
                showErrorBox("Unable to load json file.", e);
            }
        },
        PLACE: function (path) {
            try {
                let source = fs.readFileSync(path).toString();
                place_list = {};
                let PROJECT_NAME = source.match(/(?:Project:)\s*(.*)\s+/)[1];
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
                        footprint,
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
                    place_list[mark] = {
                        model: footprint,
                        footprint: footprint,
                        cox: cox * multiplier,
                        coy: coy * multiplier,
                        rot: rot,
                        top: side == "Top",
                    };
                }
                ASSEMBLER.loadSetupGUI(place_list);
            } catch (e) {
                showErrorBox("Unable to load place file.", e);
            }
        },
    },
    PREVIEW_SCALE: 1,
    zoomPreview: function (event) {
        if (event.code == "Equal" && event.ctrlKey) {
            ASSEMBLER.PREVIEW_SCALE *= 1.1;
            $("#assemble-preview-panel")
                .find(".assembler-preview-box")
                .css({
                    transform: `scale(${ASSEMBLER.PREVIEW_SCALE})`,
                });
        } else if (event.code == "Minus" && event.ctrlKey) {
            ASSEMBLER.PREVIEW_SCALE /= 1.1;
            $("#assemble-preview-panel")
                .find(".assembler-preview-box")
                .css({
                    transform: `scale(${ASSEMBLER.PREVIEW_SCALE})`,
                });
        }
    },
    build3DModel: async function (pcb_model, output_file) {
        if (output_file == undefined) return;
        let blender_io = new BlenderIO(userpref);
        await blender_io.begin();
        try {
            await blender_io.call(
                new IO_OUT("buildAssembler", {
                    pcb: pcb_model,
                    setup: ASSEMBLER.toPosition(ASSEMBLER.getSetup()),
                    out: output_file,
                })
            );
        } finally {
            blender_io.kill();
        }
        dialog.showMessageBox({
            type: "info",
            buttons: ["Ok"],
            title: "Finished generating 3D model.",
            message: "Finished generating 3D model.",
        });
    },
    make2Dimage: async function (pcb_model, output_file) {
        if (output_file == undefined) return;
        let blender_io = new BlenderIO(userpref);
        await blender_io.begin();
        try {
            await blender_io.call(
                new IO_OUT("buildAssembler", {
                    pcb: pcb_model,
                    setup: ASSEMBLER.toPosition(ASSEMBLER.getSetup()),
                    out: output_file,
                })
            );
        } finally {
            blender_io.kill();
        }
    },
    askForFile: async function ($filter_source, title) {
        let filters = [];
        for (let pair of $filter_source.attr("ext").split(";")) {
            let pair_split = pair.split(":");
            filters.push({
                name: pair_split[0],
                extensions: [pair_split[1]],
            });
        }
        let file = dialog.showOpenDialogSync({
            title: title,
            properties: ["openFile"],
            filters: filters,
        });
        return file;
    },
};
$(async function () {
    $("#assemble-container").on("keydown", ASSEMBLER.zoomPreview);
    $("#assemble-container").on("mousewheel", event => {
        if (event.originalEvent.wheelDelta > 0) {
            ASSEMBLER.zoomPreview({ code: "Equal", ctrlKey: true });
        } else {
            ASSEMBLER.zoomPreview({ code: "Minus", ctrlKey: true });
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
    $(".assembler-subsection-header").trigger("click");
    $(`.assembler-comp-src input`).on("click", async function () {
        let $this = $(this);
        let file = await ASSEMBLER.askForFile(
            $this,
            `Open ${$this.prev().text().trim()} file`
        );
        if (file != undefined) {
            $this.val(file);
            switch ($this.parent(".assembler-comp-src").attr("id")) {
                case "assembler-comp-pl-p":
                    ASSEMBLER.loadFile.PLACE(file[0]);
                    break;
                case "assembler-comp-json":
                    ASSEMBLER.loadFile.JSON(file[0]);
                    break;

                default:
                    break;
            }
        }
    });
    $("#assembler-pcb-src").on("click", async function () {
        let $this = $(this);
        let file = await ASSEMBLER.askForFile(
            $this,
            `Open ${$this.prev().text().trim()} file`
        );
        if (file != undefined) {
            $this.val(file);
        }
    });

    $("#assembler-controls :nth-child(1).div-button").on(
        "click",
        async function () {
            if (disableComponent(this)) {
                try {
                    let pcb_model = $("#assembler-pcb-src").val();
                    if (pcb_model.length == 0) {
                        throw Error("No PCB model selected.");
                    }
                    let file = dialog.showSaveDialogSync({
                        title: "Save assembled 3D model",
                        properties: [],
                        filters: [{ name: "glTF 2.0", extensions: ["glb"] }],
                    });
                    await ASSEMBLER.build3DModel(pcb_model, file);
                } catch (e) {
                    showErrorBox("Unable to build 3D model.", e);
                }
                enableComponent(this);
            }
        }
    );
    $("#assembler-controls :nth-child(2).div-button").on(
        "click",
        async function () {
            if (disableComponent(this)) {
                try {
                    let pcb_model = $("#assembler-pcb-src").val();
                    if (pcb_model.length == 0) {
                        throw Error("No PCB model selected.");
                    }
                    let file = dialog.showSaveDialogSync({
                        title: "Save assembled 3D model",
                        properties: [],
                        filters: [{ name: "PNG Image", extensions: ["png"] }],
                    });
                    await ASSEMBLER.make2Dimage(pcb_model, file);
                } catch (e) {
                    showErrorBox("Unable to build 3D model.", e);
                }
                enableComponent(this);
            }
        }
    );
    $("#assembler-controls :nth-child(3).div-button").on("click", function () {
        try {
            let file = dialog.showSaveDialogSync({
                title: "Save assembler setup to file",
                properties: [],
                filters: [{ name: "Assembler Setup", extensions: ["astp"] }],
            });
            if (file != undefined) {
                fs.writeFileSync(file, JSON.stringify(ASSEMBLER.getSetup()));
            }
        } catch (e) {
            showErrorBox("Unable to export setup.", e);
            return;
        }
    });
    $("#assembler-controls :nth-child(4).div-button").on(
        "click",
        ASSEMBLER.showPreview
    );
    $("#assembler-controls :nth-child(5).div-button").on("click", () => {
        $("#assembler-pcb-src").val("");
        $(".assembler-comp-src").find("input").val("");
        ASSEMBLER.clearSetupGUI();
    });
});
