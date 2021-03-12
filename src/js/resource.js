const themes = [];
let AUTOSAVE_DELAY = 1000;
let USE_AUTOSAVE = true;
let CURRENT_DELAY = 0;
let templates = {};
let models = {};

async function loadTemplateSpec(dir) {
    try {
        pkg = new TemplatePackage(dir);
        templates[pkg._class] = pkg;
    } catch (e) {
        showErrorBox(`Unable to load template <${dir}>\n due to error`, e);
    }
}
async function loadTemplates() {
    let promises = [];
    for (let dir of fs.readdirSync("./data/assets/templates")) {
        promises.push(
            loadTemplateSpec(`${process.cwd()}/data/assets/templates/${dir}`)
        );
    }
    for (const _promise of promises) {
        await _promise;
    }
}
async function loadModelSpec(dir) {
    try {
        let model = new ModelPackage(dir, templates);
        if (
            !fs.existsSync(model.bot_path) ||
            !fs.existsSync(model.top_path) ||
            !fs.existsSync(model.mod_path)
        ) {
            await model.makeModelAssets();
        }
        models[model._model] = model;
        appendModelBox($("#library-position-box-container"), model);
        $("#models-names").append(`<option value="${model._model}"></option>`);
    } catch (e) {
        showErrorBox(`Unable to load model ${dir}\n due to error`, e);
    }
}
async function loadModels() {
    let promises = [];
    for (let dir of fs.readdirSync("./data/assets/models")) {
        dir = `${process.cwd()}/data/assets/models/${dir}`;
        promises.push(loadModelSpec(dir));
    }
    for (const _promise of promises) {
        await _promise;
    }
}
function saveAll() {
    userpref.save();
}
function autoSave() {
    if (CURRENT_DELAY >= AUTOSAVE_DELAY) {
        CURRENT_DELAY = 0;
        saveAll();
    } else {
        CURRENT_DELAY += 100;
    }
}
function exportModel(model, file) {
    // https://www.npmjs.com/package/tar
    let dirs = ["./__top__.png", "./__bot__.png", "./__dec__.json"];
    for (let other_path of model._other) {
        dirs.push(other_path);
    }
    tar.create(
        {
            gzip: true,
            sync: true,
            file: file,
            cwd: model.package_path,
        },
        dirs
    );
}
function importModel(filepath) {
    // https://www.npmjs.com/package/tar
    let timestamp = +new Date();
    let temp_path = `./temp/${timestamp}_model`;
    fs.mkdirSync(temp_path, { recursive: true });
    try {
        tar.x({ sync: true, gzip: true, file: filepath, cwd: temp_path });
        let temp_model = new ModelPackage(temp_path, templates);
        let save_path = `${process.cwd()}/data/assets/models/${
            temp_model._model
        }`;
        console.log(save_path);
        if (
            !fs.existsSync(save_path) ||
            dialog.showMessageBoxSync({
                type: "info",
                buttons: ["Replace one in my library", "Cancel import"],
                title: "Naming collision.",
                message: `Package  "${filepath}"  you are trying to import has model name '${temp_model._model}' which is already occupierd in your model library. To solve this issue we can either reprace exisitng package with imported one, or cancel import operation. After cancelling import, no changes to your library will be done.`,
            }) == 0
        ) {
            if (!fs.existsSync(save_path))
                fs.mkdirSync(save_path, { recursive: true });
            for (let fname of fs.readdirSync(temp_path)) {
                fs.copyFileSync(
                    `${temp_path}/${fname}`,
                    `${save_path}/${fname}`
                );
            }
            loadModelSpec(save_path);
        }
    } catch (e) {
        showErrorBox("Unable to import model.", e);
    }
    if (fs.existsSync(temp_path)) fs.rmdirSync(temp_path, { recursive: true });
}
function importModelWrapper() {
    let file = dialog.showOpenDialogSync({
        title: "Select Boundle to import",
        properties: ["openFile"],
        filters: [
            { name: "Bundle", extensions: ["bundle"] },
            { name: "Archive", extensions: ["tar.gz"] },
        ],
    });
    if (file != undefined) {
        importModel(file[0]);
    }
}
function initSettingsGui() {
    /*let box = globalWorkspaceAdd.box();
    globalWorkspaceAdd.title(box, "Template Assets");
    box = globalWorkspaceAdd.box();
    globalWorkspaceAdd.title(box, "Model Assets");
    globalWorkspaceAdd.justButtons(box, [
        ["Import model asset", () => console.log("Import")],
        ["Export model asset", () => console.log("Export")],
    ]);*/
    box = globalWorkspaceAdd.box();
    globalWorkspaceAdd.title(box, "Settings");
    let themes = [];
    for (const path of fs.readdirSync("./data/assets/themes").sort()) {
        themes.push([path, path.split(".")[0]]);
    }
    globalWorkspaceAdd.entrySelect(
        box,
        "Available GUI themes",
        themes,
        "default.css",
        "gui.theme",
        function () {
            $("#theme-style").attr(
                "href",
                `../../data/assets/themes/${$(this).val()}`
            );
        }
    );
    globalWorkspaceAdd.entryNumber(
        box,
        "Font size",
        36,
        10,
        1,
        14,
        "px",
        "gui.font.size",
        function () {
            $("html").css("font-size", `${$(this).val()}px`);
        }
    );
    globalWorkspaceAdd.entryNumber(
        box,
        "Autosave delay",
        10000,
        10,
        1,
        1000,
        "ms",
        "gui.save_delay",
        function () {
            AUTOSAVE_DELAY = $(this).val();
        }
    );
    globalWorkspaceAdd.entrySelect(
        box,
        "Rendering engine",
        [
            ["EEVEE", "Eevee"],
            ["CYCLES", "Cycles"],
        ],
        "EEVEE",
        "debug.blender.engine"
    );
    globalWorkspaceAdd.entryNumber(
        box,
        "Render samples",
        256,
        1,
        1,
        32,
        "",
        "debug.blender.samples"
    );
    globalWorkspaceAdd.entryNumber(
        box,
        "Render DPI",
        3000,
        10,
        1,
        600,
        "",
        "debug.blender.dpi"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Blender in background",
        true,
        "debug.blender.background"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Keep Blender open",
        false,
        "debug.blender.keep_open"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Log JavaScript BlenderIO IN",
        false,
        "debug.log.javascript.in"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Log JavaScript BlenderIO OUT",
        false,
        "debug.log.javascript.out"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Log Python BlenderIO IN",
        true,
        "debug.log.python.in"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Log Python BlenderIO OUT",
        true,
        "debug.log.python.out"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Log userpref change",
        true,
        "debug.log.userpref",
        function () {
            userpref.log_change = $(this).prop("checked");
        }
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Extended error message JavaScript",
        false,
        "debug.log.javascript.stack"
    );
    globalWorkspaceAdd.entryToggle(
        box,
        "Open dev tools",
        true,
        "debug.dev_tools",
        function () {
            if ($(this).prop("checked")) {
                currentWebContents.openDevTools();
            } else {
                currentWebContents.closeDevTools();
            }
        }
    );
    globalWorkspaceAdd.entryClick(box, "Reload window", "reload", function () {
        currentWebContents.reload();
    });
}
