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
        dialog.showErrorBox(
            `Unable to load template <${dir}>\n due to following error:`,
            e.message
        );
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
        if (!fs.existsSync(model.bot_path)) await model.makeIcons();
        models[model._model] = model;
    } catch (e) {
        dialog.showErrorBox(
            `Unable to load model ${dir}\n due to following error:`,
            e.message
        );
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
function expotModel(model) {
    model.
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
async function initGUI() {
    initSettingsGui();
    setInterval(autoSave, 100);
    await loadTemplates();
    await loadModels();
}
$(initGUI);
