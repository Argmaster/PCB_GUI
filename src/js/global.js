const themes = [];
let AUTOSAVE_DELAY = 1000;
let USE_AUTOSAVE = true;
let CURRENT_DELAY = 0;


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
function initSettingsGui() {
    globalWorkspaceAdd.box();
    globalWorkspaceAdd.title("Template Assets");
    globalWorkspaceAdd.box();
    globalWorkspaceAdd.title("Model Assets");
    globalWorkspaceAdd.box();
    globalWorkspaceAdd.title("Settings");
    let themes = [];
    for (const path of fs.readdirSync("./data/assets/themes").sort()) {
        themes.push([path, path.split(".")[0]]);
    }
    globalWorkspaceAdd.entrySelect(
        "Available GUI themes",
        themes,
        "default.css",
        "gui.theme",
        userpref,
        $this =>
            $("#theme-style").attr(
                "href",
                `../../data/assets/themes/${$this.val()}`
            )
    );
    globalWorkspaceAdd.entryNumber(
        "Font size",
        36,
        10,
        1,
        14,
        "px",
        "gui.font.size",
        userpref,
        $this => $("html").css("font-size", `${$this.val()}px`)
    );
    globalWorkspaceAdd.entryNumber(
        "Autosave delay",
        10000,
        10,
        1,
        1000,
        "ms",
        "gui.save_delay",
        userpref,
        $this => (AUTOSAVE_DELAY = $this.val())
    );
    globalWorkspaceAdd.entrySelect(
        "Rendering engine",
        [
            ["EEVEE", "Eevee"],
            ["CYCLES", "Cycles"],
        ],
        "EEVEE",
        "debug.blender.engine",
        userpref
    );
    globalWorkspaceAdd.entryNumber(
        "Render samples",
        256,
        1,
        1,
        32,
        "",
        "debug.blender.samples",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Blender in background",
        true,
        "debug.blender.background",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Keep Blender open",
        false,
        "debug.blender.keep_open",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Log JavaScript BlenderIO IN",
        false,
        "debug.log.javascript.in",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Log JavaScript BlenderIO OUT",
        false,
        "debug.log.javascript.out",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Log Python BlenderIO IN",
        true,
        "debug.log.python.in",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Log Python BlenderIO OUT",
        true,
        "debug.log.python.out",
        userpref
    );
    globalWorkspaceAdd.entryToggle(
        "Log userpref change",
        true,
        "debug.log.userpref",
        userpref,
        $this => (userpref.log_change = $this.prop("checked"))
    );
    globalWorkspaceAdd.entryToggle(
        "Open dev tools",
        true,
        "debug.dev_tools",
        userpref,
        $this => {
            if ($this.prop("checked")) {
                currentWebContents.openDevTools();
            } else {
                currentWebContents.closeDevTools();
            }
        }
    );
    globalWorkspaceAdd.entryClick("Reload window", "reload", $this =>
        currentWebContents.reload()
    );
}
function initBookmarks() {
    $(".bookmark-box").each(function (index) {
        $(this).attr("id", `bk${index}`);
        $(this).on("click", () => toggleBookmark(index));
    });
    $(".workspace-box").each(function (index) {
        $(this).attr("id", `ws${index}`);
    });
    function toggleBookmark(index) {
        const bookmark = $(`#bk${index}`);
        if (!bookmark.hasClass("bookmark-active")) {
            // togle bookmark highlight
            $(".bookmark-active").each(function () {
                $(this).addClass("bookmark-inactive");
                $(this).removeClass("bookmark-active");
            });
            bookmark.addClass("bookmark-active");
            bookmark.removeClass("bookmark-inactive");
            // show workspace
            $(".workspace-box").each(function () {
                $(this).hide();
            });
            var workspace = $(`#ws${index}`);
            workspace.show();
        }
    }
    toggleBookmark(0);
}
function initGUI() {
    initSettingsGui();
    setInterval(autoSave, 100);
    initBookmarks();
}
$(initGUI);
