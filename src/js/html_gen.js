function getParamAnyHTML(model, prm_dict, param_name, param_id, userpref) {
    let _default = prm_dict[param_name];
    let _user_pref = userpref.getModelProp(model._model, param_id);
    if (_user_pref == undefined) {
        _user_pref = _default;
    }
    if (typeof _default != "string") {
        _default = JSON.stringify(_default);
    }
    return `
        <div class="model-edit-param-box">
            <div class="model-edit-param-label">
                ${param_name}
            </div>
            <input
                type="text"
                class="standard-text-input model-edit-param-input"
                placeholder=${_default}
                ttype="${model.template.tem_dict[param_name].ttype}"
                savetype="Simple"
                param_id="${param_id}"
                default="${_default}"
                value="${_user_pref}"
            />
        </div>`;
}
function getParamNumberHTML(model, prm_dict, param_name, param_id, userpref) {
    let param_template = model.template.tem_dict[param_name];
    let _default = prm_dict[param_name];
    let _user_pref = userpref.getModelProp(model._model, param_id);
    if (_user_pref == undefined) {
        _user_pref = _default;
    }
    let step = 1;
    if (param_template.ttype == "Float") {
        step = (param_template.range[1] - param_template.range[0]) / 100;
    }
    return `
        <div class="model-edit-param-box">
            <div class="model-edit-param-label">
                ${param_name}
            </div>
            <input
                type="number"
                class="standard-text-input model-edit-param-input"
                placeholder=${_default}
                ttype="${param_template.ttype}"
                savetype="Simple"
                param_id="${param_id}"
                default="${_default}"
                value="${_user_pref}"
                min="${param_template.range[0]}"
                max="${param_template.range[1]}"
                step="${step}"
                inclusive="${param_template.inclusive}"
            />
        </div>`;
}
function getParamBoolHTML(model, prm_dict, param_name, param_id, userpref) {
    let _default = prm_dict[param_name];
    let _user_pref = userpref.getModelProp(model._model, param_id);
    if (_user_pref == undefined) {
        _user_pref = _default;
    }
    return `
        <div class="model-edit-param-box">
            <div class="model-edit-param-label">
                ${param_name}
            </div>
            <select
                class="standard-text-input"
                savetype="Simple"
                ttype="Keyword"
                param_id="${param_id}"
                default="${_default}"
            >
                <option value="true" ${
                    _user_pref ? "selected" : ""
                }>True</option>
                <option value="false" ${
                    !_user_pref ? "selected" : ""
                }>False</option>
            </select>
        </div>`;
}
function getParamKeywordHTML(model, prm_dict, param_name, param_id, userpref) {
    let _default = prm_dict[param_name];
    let _user_pref = userpref.getModelProp(model._model, param_id);
    if (_user_pref == undefined) {
        _user_pref = _default;
    }
    let options_html = "";
    for (const val of model.template.tem_dict[param_name].options) {
        if (val == _user_pref) {
            options_html += `<option value="${val}" selected>${val}</option>`;
        } else {
            options_html += `<option value="${val}">${val}</option>`;
        }
    }
    return `
        <div class="model-edit-param-box">
            <div class="model-edit-param-label">
                ${param_name}
            </div>
            <select
                class="standard-text-input"
                ttype="Keyword"
                savetype="Simple"
                param_id="${param_id}"
                default="${_default}"
            >
                ${options_html}
            </select>
        </div>`;
}
const MATERIAL_DEFAULT = {
    color: [0.0, 0.0, 0.0, 1.0],
    subsurface: 0.0,
    subsurfaceRadius: [0.0, 0.0, 0.0, 1.0],
    subsurfaceColor: [0.0, 0.0, 0.0, 1.0],
    metallic: 0.0,
    specular: 0.5,
    specularTint: 0.0,
    roughness: 1.0,
    anisotropic: 0.0,
    anisotropicRotation: 0.0,
    sheen: 0.0,
    sheenTint: 0.5,
    clearcoat: 0.0,
    clearcoatRoughness: 0.03,
    IOR: 1.45,
    transmission: 0.0,
    transmissionRoughness: 0.0,
    emission: [0.0, 0.0, 0.0, 1.0],
    emissionStrength: 1.0,
    alpha: 1.0,
};
const MATERIAL_TEMPLATE = {
    color: {
        ttype: "Vector",
        values: [
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
        ],
        default: [0.0, 0.0, 0.0, 1.0],
    },
    subsurface: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    subsurfaceRadius: {
        ttype: "Vector",
        values: [
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
        ],
        default: [0.0, 0.0, 0.0, 1.0],
    },
    subsurfaceColor: {
        ttype: "Vector",
        values: [
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
        ],
        default: [0.0, 0.0, 0.0, 1.0],
    },
    metallic: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    specular: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    specularTint: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    roughness: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    anisotropic: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    anisotropicRotation: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    sheen: { ttype: "Float", range: [0.0, 1.0], inclusive: true },
    sheenTint: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    clearcoat: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    clearcoatRoughness: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    IOR: { ttype: "Float", range: [0.0, 5.0], inclusive: true, default: 1.45 },
    transmission: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    transmissionRoughness: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    emission: {
        ttype: "Vector",
        values: [
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
                inclusive: true,
            },
        ],
        default: [0.0, 0.0, 0.0, 1.0],
    },
    emissionStrength: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
    alpha: {
        ttype: "Float",
        range: [0.0, 1.0],
        inclusive: true,
    },
};
function getParamMaterialParamsHTML(
    model,
    prm_dict,
    param_name,
    param_id,
    userpref
) {
    let property_html = "";
    let params = {};
    Object.assign(params, MATERIAL_DEFAULT);
    Object.assign(params, prm_dict);
    for (let prop_name in MATERIAL_TEMPLATE) {
        property_html += exports.getModelParamSwitchHTML(
            {
                _model: model._model,
                template: {
                    tem_dict: MATERIAL_TEMPLATE,
                },
            },
            params,
            prop_name,
            param_id + prop_name,
            userpref
        );
    }
    return `
    <div class="model-edit-param-box">
        <div class="model-edit-input-indent-block">
            <div class="model-edit-indent-block-label">
                ${param_name}
            </div>
            ${property_html}
        </div>
    </div>`;
}
function getParamVectorHTML(model, prm_dict, param_name, param_id, userpref) {
    let property_html = "";
    let param_template = model.template.tem_dict[param_name];
    let _default = prm_dict[param_name];
    for (let index in param_template.values) {
        property_html += exports.getModelParamSwitchHTML(
            {
                _model: model._model,
                template: {
                    tem_dict: param_template.values,
                },
            },
            _default,
            index,
            param_id + index,
            userpref
        );
    }
    return `
    <div class="model-edit-param-box">
        <div class="model-edit-input-indent-block">
            <div class="model-edit-indent-block-label">
                ${param_name}
            </div>
            <div class="model-edit-vector-value-block">
                ${property_html}
            </div>
        </div>
    </div>`;
}
exports.getModelParamSwitchHTML = function (
    model,
    prm_dict,
    param_name,
    param_id,
    userpref
) {
    switch (model.template.tem_dict[param_name].ttype) {
        case "String":
        case "ExistingFilePath":
        case "ExistingDirPath":
        case "AnyPath":
        case "Angle":
        case "UnitOfLength":
            return getParamAnyHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );

        case "Int":
        case "Float":
            return getParamNumberHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );

        case "Keyword":
            return getParamKeywordHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );

        case "Bool":
            return getParamBoolHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );

        case "MaterialParams":
            return getParamMaterialParamsHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );

        case "Vector":
            return getParamVectorHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );

        case "NestedTemplate":
            console.log(model.template.tem_dict[param_name].ttype);
            break;

        default:
            return getParamAnyHTML(
                model,
                prm_dict,
                param_name,
                param_id,
                userpref
            );
    }
};
exports.getModelContainerHTML = function (model) {
    return `
    <div class="model-box">
        <div class="model-data">
            <div class="model-image">
                <img class="model-icon" src="${model.package_path}/__top__.png"/>
                <img class="model-icon model-icon-disable" src="${model.package_path}/__bot__.png"/>
            </div>
            <div class="model-meta">
                <div class="model-title">
                    <span class="model-title-small">model</span>
                    <span class="model-name">${model._model}</span>
                    <span class="model-title-small">class</span>
                    <span class="model-class">${model._class}</span>
                </div>
                <div class="model-meta-row">
                    <div class="model-meta-label">Author:</div>
                    <div class="model-meta-value">${model._author}</div>
                </div>
                <div class="model-meta-row">
                    <div class="model-meta-label">About:</div>
                    <div class="model-meta-value">${model._dscp}</div>
                </div>
            </div>
        </div>
        <div class="model-corner-box">
            <div class="model-modification-mark"></div>
            <div class="model-modification-mark model-modification-mark-active"></div>
            <div class="model-modification-mark model-modification-mark-active"></div>
            <div class="div-button model-edit-button" name="${model._model}">Edit</div>
        </div>
    </div>`;
};
exports.genEditModelMenuHTML = function (model, userpref) {
    let vx = userpref.getModelProp(model._model, "$__Xaxis");
    if (vx == undefined) {
        vx = 0;
    }
    let vy = userpref.getModelProp(model._model, "$__Yaxis");
    if (vy == undefined) {
        vy = 0;
    }
    return `
    <div class="model-edit-title">
        <span class="model-title-small">model</span>
        <span class="model-name">${model._model}</span>
        <span class="model-title-small">class</span>
        <span class="model-class">${model._class}</span>
    </div>
    <div class="model-edit-pinroot">
        <div class="model-edit-pinroot-img-box">
            <img class="model-edit-pinroot-img" src="${model.package_path}/__bot__.png"/>
            <div class="pin-ptr">
                <span></span>
            </div>
        </div>
        <div class="model-edit-pinroot-data">
            <div>
                <div class="model-edit-pinroot-data-label">X</div>
                <input
                    type="number"
                    class="standard-text-input model-edit-pinroot-data-input"
                    value="${vx}"
                    id="Xaxis"
                />
            </div>
            <div>
                <div class="model-edit-pinroot-data-label">Y</div>
                <input
                    type="number"
                    class="standard-text-input model-edit-pinroot-data-input"
                    value="${vy}"
                    id="Yaxis"
                />
            </div>
        </div>
    </div>
    `;
};
