function init3DModelGUI() {
    const model_container = $("#resource-model-container-container");
    for (const key in models) {
        appendModelBox(model_container, models[key]);
    }
}
function init3DModelEditMenu($this, model) {
    $(".resource-model-container").each(function () {
        $(this).removeClass("resource-model-container-active");
    });
    try {
        $this.addClass("resource-model-container-active");
        let panel = $("#model-edit-panel");
        ACTIVE_MODEL = model;
        modelWorkspaceAdd.editMenu(panel);
        modelWorkspaceAdd.template(panel, "Properties", "");
    } catch (e) {
        dialog.showErrorBox(
            "Unable to load model edit menu due to error",
            e.message
        );
    }
}
$(init3DModelGUI);
