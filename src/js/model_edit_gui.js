const MATERIAL_TEMPLATE = {
    color: {
        ttype: "Color",
    },
    subsurface: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    subsurfaceRadius: {
        ttype: "Vector",
        template: [
            {
                ttype: "Float",
                range: [0.0, 1.0],
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
            },
            {
                ttype: "Float",
                range: [0.0, 1.0],
            },
        ],
    },
    subsurfaceColor: {
        ttype: "Color",
    },
    metallic: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    specular: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    specularTint: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    roughness: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    anisotropic: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    anisotropicRotation: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    sheen: { ttype: "Float", range: [0.0, 1.0] },
    sheenTint: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    clearcoat: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    clearcoatRoughness: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    IOR: { ttype: "Float", range: [0.0, 5.0] },
    transmission: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    transmissionRoughness: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    emission: {
        ttype: "Color",
    },
    emissionStrength: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
    alpha: {
        ttype: "Float",
        range: [0.0, 1.0],
    },
};
function RNAtoTemplate(model, rna) {
    let outcome = model.template.tem_dict;
    if (rna.length == 0) {
        return outcome;
    }
    for (let comp of rna.split(".")) {
        outcome = outcome[comp];
        if (outcome == undefined)
            throw Error(`Template: RNA is mallformed ${rna}`);
        else if (outcome.ttype == "MaterialParams") outcome = MATERIAL_TEMPLATE;
        else if (outcome.ttype == "Vector") outcome = outcome.template;
        else if (outcome.ttype == "NestedTemplate") outcome = outcome.template;
    }
    return outcome;
}
function RNAtoTType(model, rna) {
    let outcome = model.template.tem_dict;
    if (rna.length == 0) {
        return outcome;
    }
    rna = rna.split(".");
    for (let i = 0; i < rna.length; i++) {
        outcome = outcome[rna[i]];
        if (outcome == undefined)
            throw Error(`Template: RNA is mallformed ${rna}`);
        if (i + 1 < rna.length) {
            if (outcome.ttype == "MaterialParams") outcome = MATERIAL_TEMPLATE;
            else if (outcome.ttype == "Vector") outcome = outcome.template;
            else if (outcome.ttype == "NestedTemplate")
                outcome = outcome.template;
        }
    }
    return outcome.ttype;
}
const MATERIAL_DEFAULT = {
    color: "#FFFFFFFF",
    subsurface: 0.0,
    subsurfaceRadius: [0.0, 0.0, 0.0],
    subsurfaceColor: "#FFFFFFFF",
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
    emission: "#FFFFFFFF",
    emissionStrength: 0.0,
    alpha: 1.0,
};
function RNAtoParam(model, rna) {
    let outcome = model.prm_dict;
    if (rna.length == 0) {
        return outcome;
    }
    let dna = [];
    for (let comp of rna.split(".")) {
        dna.push(comp);
        outcome = outcome[comp];
        if (outcome == undefined)
            throw Error(
                `Unable to access param value for model ${ACTIVE_MODEL._model} at RNA "${rna}"`
            );
        if (RNAtoTType(model, dna.join(".")) == "MaterialParams")
            outcome = Object.assign({}, MATERIAL_DEFAULT, outcome);
    }
    return outcome;
}
function entry_status_ok(thing) {
    thing.removeClass("text-input-mistake");
    thing.addClass("text-input-changed");
}
function entry_status_error(thing) {
    thing.removeClass("text-input-changed");
    thing.addClass("text-input-mistake");
}
function entry_status_clear(thing) {
    thing.removeClass("text-input-changed");
    thing.removeClass("text-input-mistake");
}
let ACTIVE_MODEL = null;
modelWorkspaceAdd = {
    entryValidatable: function (
        $target, // jQuery object !
        _label, // entry label
        _rna, // entry userpref rna
        _default // default value
    ) {
        let _user_pref = userpref.getModelRNA(
            ACTIVE_MODEL._model,
            _rna,
            _default
        );
        $target.append(
            `<div class="edit-entry-row">
                <div class="edit-entry-row-label">
                    ${_label}
                </div>
                <input
                    type="text"
                    class="standard-text-input edit-param-entry"
                    placeholder=${_default}
                    RNA="${_rna}"
                    value="${_user_pref}"
                />
            </div>`
        );
        return $target.find(".edit-entry-row").last().find("input");
    },
    String: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let $this = this.entryValidatable(
            $target, // jQuery object !
            _label, // entry label
            _rna, // entry userpref rna
            _default // default value,
        );
        $this.on("input", function () {
            let raw_val = $this.val();
            entry_status_clear($this);
            if (raw_val != _default) {
                userpref.setModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                entry_status_ok($this);
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            }
        });
        $this.trigger("input");
        return $this;
    },
    UnitOfLength: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let $this = this.entryValidatable(
            $target, // jQuery object !
            _label, // entry label
            _rna, // entry userpref rna
            _default // default value,
        );
        $this.on("input", function () {
            let raw_val = $this.val();
            let val = TType.UnitOfLength(raw_val);
            entry_status_clear($this);
            if (raw_val != _default) {
                if (!isNaN(val)) {
                    userpref.setModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                    entry_status_ok($this);
                } else {
                    userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                    entry_status_error($this);
                }
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            }
        });
        $this.trigger("input");
        return $this;
    },
    Color: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let $this = this.entryValidatable(
            $target, // jQuery object !
            _label, // entry label
            _rna, // entry userpref rna
            _default // default value
        );
        $this.on("input", function () {
            let raw_val = $this.val();
            let val = TType.Color(raw_val);
            entry_status_clear($this);
            if (raw_val != _default) {
                if (typeof val == "object") {
                    userpref.setModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                    entry_status_ok($this);
                } else {
                    userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                    entry_status_error($this);
                }
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            }
        });
        $this.trigger("input");
        return $this;
    },
    Angle: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let $this = this.entryValidatable(
            $target, // jQuery object !
            _label, // entry label
            _rna, // entry userpref rna
            _default // default value
        );
        $this.on("input", function () {
            let raw_val = $this.val();
            let val = TType.Angle(raw_val);
            entry_status_clear($this);
            if (raw_val != _default) {
                if (!isNaN(val)) {
                    userpref.setModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                    entry_status_ok($this);
                } else {
                    userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
                    entry_status_error($this);
                }
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            }
        });
        $this.trigger("input");
        return $this;
    },
    Float: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let $this = this.entryValidatable(
            $target, // jQuery object !
            _label, // entry label
            _rna, // entry userpref rna
            _default // default value
        );
        let template = RNAtoTemplate(ACTIVE_MODEL, _rna);
        $this.on("input", function () {
            let raw_val = $this.val();
            let val = parseFloat(raw_val);
            entry_status_clear($this);
            if (val != _default) {
                if (
                    !isNaN(val) &&
                    val >= template.range[0] &&
                    val <= template.range[1]
                ) {
                    userpref.setModelRNA(ACTIVE_MODEL._model, _rna, val);
                    entry_status_ok($this);
                } else {
                    userpref.delModelRNA(ACTIVE_MODEL._model, _rna);
                    entry_status_error($this);
                }
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna);
            }
        });
        $this.trigger("input");
        return $this;
    },
    Int: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let $this = this.entryValidatable(
            $target, // jQuery object !
            _label, // entry label
            _rna, // entry userpref rna
            _default // default value
        );
        let template = RNAtoTemplate(ACTIVE_MODEL, _rna);
        $this.on("input", function () {
            let raw_val = $this.val();
            let val = parseInt(raw_val);
            entry_status_clear($this);
            if (val != _default) {
                if (
                    !isNaN(val) &&
                    val >= template.range[0] &&
                    val <= template.range[1]
                ) {
                    userpref.setModelRNA(ACTIVE_MODEL._model, _rna, val);
                    entry_status_ok($this);
                } else {
                    userpref.delModelRNA(ACTIVE_MODEL._model, _rna);
                    entry_status_error($this);
                }
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna);
            }
        });
        $this.trigger("input");
        return $this;
    },
    boolean: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let _user_pref = userpref.getModelRNA(
            ACTIVE_MODEL._model,
            _rna,
            _default
        );
        $target.append(
            `<div class="edit-entry-row">
                <div class="edit-entry-row-label">
                    ${_label}
                </div>
                <label class="switch">
                    <input
                        type="checkbox"
                        RNA="${_rna}"
                    />
                    <span class="slider round"></span>
                </label>
            </div>`
        );
        let $this = $target.find(".edit-entry-row").last().find("input");
        $this.attr("checked", _user_pref);
        $this.on("input", function () {
            entry_status_clear($this.parent("span"));
            let raw_val = $this.prop("checked");
            if (raw_val != _default) {
                entry_status_ok($this.parent("span"));
                userpref.setModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            }
        });
        return $this;
    },
    keyword: function ($target, _label, _rna) {
        let _default = RNAtoParam(ACTIVE_MODEL, _rna);
        let _user_pref = userpref.getModelRNA(
            ACTIVE_MODEL._model,
            _rna,
            _default
        );
        let options_html = "";
        for (const val of RNAtoTemplate(ACTIVE_MODEL, _rna).options) {
            options_html += `<option value="${val}">${val}</option>`;
        }
        $target.append(
            `<div class="edit-entry-row">
                <div class="edit-entry-row-label">
                    ${_label}
                </div>
                <select
                    class="standard-text-input"
                    RNA="${_rna}"
                >
                ${options_html}
                </select>
            </div>`
        );
        let $this = $target.find(".edit-entry-row").last().find("select");
        $this.val(_user_pref);
        $this.on("change", function () {
            entry_status_clear($this);
            let raw_val = $this.val();
            if (raw_val != _default) {
                entry_status_ok($this);
                userpref.setModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            } else {
                userpref.delModelRNA(ACTIVE_MODEL._model, _rna, raw_val);
            }
        });
        return $this;
    },
    Switch: function ($target, _ttype, _label, _rna) {
        switch (_ttype) {
            case "UnitOfLength":
                return this.UnitOfLength($target, _label, _rna);
            case "Color":
                return this.Color($target, _label, _rna);
            case "Angle":
                return this.Angle($target, _label, _rna);
            case "Float":
                return this.Float($target, _label, _rna);
            case "Int":
                return this.Int($target, _label, _rna);
            case "Keyword":
                return this.keyword($target, _label, _rna);
            case "Bool":
                return this.boolean($target, _label, _rna);
            case "MaterialParams":
            case "Vector":
            case "NestedTemplate":
                return this.template($target, _label, _rna);
            case "ExistingFilePath":
            case "ExistingDirPath":
            case "PathExpression":
            case "String":
                return this.String($target, _label, _rna);
            default:
                throw Error(`Unsupported TType: ${_ttype}`);
        }
    },
    template: function ($target, _label, _rna) {
        $target.append(
            `<div class="edit-entry-row">
                <div class="edit-indent-block">
                    <div class="edit-indent-label">
                        ${_label}
                    </div>
                </div>
            </div>`
        );
        let $this = $target.find(".edit-indent-block").last();
        let _template = RNAtoTemplate(ACTIVE_MODEL, _rna);
        for (let key in _template) {
            this.Switch(
                $this,
                _template[key].ttype,
                key,
                _rna.length > 0 ? `${_rna}.${key}` : key
            );
        }
        return $this;
    },
    editMenu: $target => {
        $target.empty();
        $target.append(`
        <div class="model-edit-title">
            <span class="model-title-small">model</span>
            <span class="model-name">${ACTIVE_MODEL._model}</span>
            <span class="model-title-small">class</span>
            <span class="model-class">${ACTIVE_MODEL._class}</span>
        </div>
        <div class="model-edit-pinroot">
            <div class="model-edit-pinroot-img-box">
                <img class="model-edit-pinroot-img" src="${
                    ACTIVE_MODEL.package_path
                }/__bot__.png" onerror="this.src='../../data/assets/img/img-broken.svg';"/>
                <div class="pin-ptr">
                    <span></span>
                </div>
            </div>
            <div class="model-edit-pinroot-data">
                <div>
                    <span>offset X</span>
                    <input
                        type="number"
                        class="standard-text-input"
                        value="${userpref.getModelRNA(
                            ACTIVE_MODEL._model,
                            "$Xaxis",
                            0
                        )}"
                        RNA="$Xaxis"
                    />
                </div>
                <div>
                    <span>offset Y</span>
                    <input
                        type="number"
                        class="standard-text-input"
                        value="${userpref.getModelRNA(
                            ACTIVE_MODEL._model,
                            "$Yaxis",
                            0
                        )}"
                        RNA="$Yaxis"
                    />
                </div>
                <div>
                    <span>Rotation</span>
                    <input
                        type="number"
                        class="standard-text-input"
                        value="${userpref.getModelRNA(
                            ACTIVE_MODEL._model,
                            "$Angle",
                            0
                        )}"
                        RNA="$Angle"
                    />
                </div>
                <div>
                    <div class="div-button" id="export-model">
                        Export Model
                    </div>
                    <div class="div-button" id="delete-model">
                        Delete Model
                    </div>
                </div>
            </div>
        </div>
        <div class="model-edit-param-container"></div>
        `);
        {
            let Xaxis = $target.find(`input[RNA="$Xaxis"]`);
            let Yaxis = $target.find(`input[RNA="$Yaxis"]`);
            let Angle = $target.find(`input[RNA="$Angle"]`);
            $(".pin-ptr").draggable({ containment: "parent" });
            $(".pin-ptr").on("drag", function (event, ui) {
                Xaxis.val(ui.position.left - 150);
                Xaxis.trigger("input");
                Yaxis.val((ui.position.top - 150) * -1);
                Yaxis.trigger("input");
            });
            Xaxis.on("input", function () {
                let value = parseFloat(Xaxis.val());
                if (value > 150) {
                    value = 150;
                } else if (value < -150) {
                    value = -150;
                }
                Xaxis.val(value);
                userpref.setModelRNA(ACTIVE_MODEL._model, "$Xaxis", value);
                $(".pin-ptr").css({ left: value + 150 });
            });
            Yaxis.on("input", function () {
                let value = parseFloat(Yaxis.val());
                if (value > 150) {
                    value = 150;
                } else if (value < -150) {
                    value = -150;
                }
                userpref.setModelRNA(ACTIVE_MODEL._model, "$Yaxis", value);
                Yaxis.val(value);
                $(".pin-ptr").css({ top: value * -1 + 150 });
            });
            Angle.on("input", function () {
                let value = parseFloat(Angle.val());
                if (value > 359) {
                    value = 359;
                } else if (value < 0) {
                    value = 0;
                }
                Angle.val(value);
                userpref.setModelRNA(ACTIVE_MODEL._model, "$Angle", value);
                $(".pin-ptr").css({ top: value * -1 + 150 });
            });
        }
        $("#export-model").on("click", () => exportModel(ACTIVE_MODEL));
    },
};
let appendModelBox = function ($target, model) {
    $target.append(
        `<div class="resource-model-container">
            <div class="resource-model-data">
                <div class="model-image">
                    <img src="${model.package_path}/__top__.png" onerror="this.src='../../data/assets/img/img-broken.svg';"/>
                    <img class="model-icon-disable" src="${model.package_path}/__bot__.png" onerror="this.src='../../data/assets/img/img-broken.svg';"/>
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
                <div class="model-modification-mark model-modification-mark-active"></div>
                <div class="model-modification-mark model-modification-mark-active"></div>
                <div class="model-modification-mark model-modification-mark-active"></div>
                <div class="div-button model-edit-button">More</div>
                <div class="div-button model-edit-button"">Make</div>
            </div>
        </div>`
    );
    let $this = $target.find(".resource-model-container").last();
    $this.find(".model-image").on("click", function () {
        $(this).find("img").toggle();
    });
    $this
        .find(":nth-child(4).model-edit-button")
        .on("click", () => init3DModelEditMenu($this, model));
    $this
        .find(":nth-child(5).model-edit-button")
        .on("click", async function () {
            $(this).addClass("breath-div-button");
            try {
                await model.make();
            } finally {
                $(this).removeClass("breath-div-button");
            }
        });
};