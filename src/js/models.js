const pF = require("../js/param_filers");
const TemplatePackage = require("../js/template").TemplatePackage;
const ModelPackage = require("../js/model").ModelPackage;
const up = require("../js/userpref");
const {
    getModelParamSwitchHTML,
    getModelContainerHTML,
    genEditModelMenuHTML,
} = require("../js/html_gen");

let templates = {};
let models = {};

async function loadTemplateSpec(dir) {
    try {
        pkg = new TemplatePackage(dir);
        templates[pkg._class] = pkg;
    } catch (e) {
        alert(`Unable to load template <${dir}> due to error: ${e}`);
    }
}
async function loadTemplates() {
    let promises = [];
    for (let dir of fs.readdirSync("./data/assets/templates")) {
        try {
            promises.push(
                loadTemplateSpec(
                    `${process.cwd()}/data/assets/templates/${dir}`
                )
            );
        } catch (e) {
            alert(`Unable to load template <${dir}> due to error: ${e}`);
        }
    }
    for (const _promise of promises) {
        await _promise;
    }
}
async function loadModelSpec(dir) {
    try {
        let model = new ModelPackage(dir, templates);
        if (!fs.existsSync(model.bot_path))
            await model.makeIcons();
        models[model._model] = model;
    } catch (e) {
        alert(`Unable to load model <${dir}> due to error: ${e}`);
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
function attachFilters(model) {
    // ttype String
    // ttype Path (any)
    $("[ttype=String]").on("input", pF.String);
    // ttype Keyword
    // ttype Bool
    $("[ttype=Keyword]").on("input", pF.String);
    // ttype UnitOfLength
    $("[ttype=UnitOfLength]").on("input", pF.UnitOfLength);
    // ttype Int
    $("[ttype=Int]").on("input", pF.Int);
    // ttype Float
    $("[ttype=Float]").on("input", pF.Float);
    $("[savetype=Simple]").on("input", function () {
        up.saveSimpleProp(userpref, model, this);
    });
    $(".model-edit-pinroot-data-input").on("input", function () {
        up.savePinrootPtr(userpref, model, this);
    });
    $("*").trigger("input");
}
function attachPtrDraggable() {
    $(".pin-ptr").draggable({ containment: "parent" });
    $(".pin-ptr").on("drag", function (event, ui) {
        $("#Xaxis").val(ui.position.left - 150);
        $("#Xaxis").trigger("input");
        $("#Yaxis").val((ui.position.top - 150) * -1);
        $("#Yaxis").trigger("input");
    });
    $("#Xaxis").on("input", function () {
        let value = parseFloat($(this).val());
        if (value > 150) {
            value = 150;
        } else if (value < -150) {
            value = -150;
        }
        $(this).val(value);
        $(".pin-ptr").css({ left: value + 150 });
    });
    $("#Yaxis").on("input", function () {
        let value = parseFloat($(this).val());
        if (value > 150) {
            value = 150;
        } else if (value < -150) {
            value = -150;
        }
        $(this).val(value);
        $(".pin-ptr").css({ top: value * -1 + 150 });
    });
}
function loadEditModelMenu() {
    $(".model-box").each(function () {
        $(this).removeClass("model-box-active");
    });
    $(this).parents(".model-box").addClass("model-box-active");
    let panel = $("#model-edit-panel");
    let model = models[$(this).attr("name")];
    panel.empty();
    panel.append(genEditModelMenuHTML(model, userpref));
    attachPtrDraggable();
    let model_params_html = "";
    for (const param_name in model.template.tem_dict) {
        model_params_html += getModelParamSwitchHTML(
            model,
            model.prm_dict,
            param_name,
            param_name,
            userpref,
            param_name
        );
    }
    panel.append(`
    <div class="model-edit-param-container">
        ${model_params_html}
    </div>`);
    attachFilters(model);
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
