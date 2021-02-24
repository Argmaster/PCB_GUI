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
function loadModelGUI() {
    const model_container = $("#model-box-container");
    for (const key in models) {
        model_container.append(getModelContainerHTML(models[key]));
    }
}
function loadEditModelMenu() {
    $(".model-box").each(function () {
        $(this).removeClass("model-box-active");
    });
    try {
        $(this).parents(".model-box").addClass("model-box-active");
        let panel = $("#model-edit-panel");
        ACTIVE_MODEL = models[$(this).attr("name")];
        modelWorkspaceAdd.editMenu(panel);
        modelWorkspaceAdd.template(panel, "Properties", "");
    } catch (e) {
        dialog.showErrorBox(
            "Unable to load model edit menu due to error",
            e.message
        );
    }
}
async function initializeAssets() {
    await loadTemplates();
    await loadModels();
    loadModelGUI();
    $(".model-image").each(function () {
        $(this).on("click", function () {
            $(this).find(".model-icon").toggle();
            $(this).find(".model-pins").toggle();
        });
    });
    $(".model-edit-button").each(function () {
        $(this).on("click", loadEditModelMenu);
    });
}
$(initializeAssets);
