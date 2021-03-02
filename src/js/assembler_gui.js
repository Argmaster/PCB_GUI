/*
let out = {
    project: "",
    units: "",
    components: {}
};
*/
function addAssemblerComponent(signature, model, label, cox, coy, rot, top) {
    $("#assembler-components-list").append(
        `<div class="assembler-component-body">
            <div class="assembler-component-body-title"><div>&#x203A;</div>${signature} ${model}</div>
            <div class="assembler-component-body-inner">
                <div class="assembler-component-body-row">
                    <div>model</div>
                    <input class="standard-text-input" value="${model}" list="models-names" />
                    <div>label</div>
                    <input class="standard-text-input" value="${label}" />
                </div>
                <div class="assembler-component-body-row">
                    <div>co. X</div>
                    <input class="standard-text-input assembler-short" value="${cox}" />
                    <div>co. Y</div>
                    <input class="standard-text-input assembler-short" value="${coy}" />
                </div>
                <div class="assembler-component-body-row">
                    <div>Rot</div>
                    <input class="standard-text-input assembler-short" value="${rot}" />
                    <div>Top</div>
                    <label class="switch">
                        <input type="checkbox" />
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
let ASSEMBLER_PROJECT_NAME = "";
let ASSEMBLER_PARTSLIST_COMPONENTS_LIST = {};
let ASSEMBLER_PLACE_POSITION_LIST = {};
const loadComponents = {
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
            dialog.showErrorBox("Unable to load parts list file.", e.stack);
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
            dialog.showErrorBox("Unable to load place file.", e.stack);
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
$(function () {
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
});
