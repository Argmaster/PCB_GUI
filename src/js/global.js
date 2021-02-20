const themes = [];
let AUTOSAVE_DELAY = 1000;
let USE_AUTOSAVE = true;
let CURRENT_DELAY = 0;


function loadThemes() {
    for (const path of fs.readdirSync("./data/assets/themes").sort()) {
        $("#theme-select").append(
            `<option value="${path}">${path.split(".")[0]}</option>`
        );
    }
    let theme_pref = userpref.getUserPref("gui_pref", "theme");
    if (theme_pref == undefined) {
        theme_pref = "default.css";
    }
    $("#theme-select").val(theme_pref);
    selectTheme();
}
function selectTheme() {
    let theme_name = $("#theme-select").val();
    userpref.setUserPref("gui_pref", "theme", theme_name);
    $("#theme-style").attr("href", `../../data/assets/themes/${theme_name}`);
}
function changeFontSize() {
    let $this = $(this);
    let value = parseInt($this.val());
    if (
        !isNaN(value) &&
        value >= $this.attr("min") &&
        value <= $this.attr("max")
    ) {
        userpref.setUserPref("gui_pref", "font_size", value);
        $("html").css("font-size", value);
    }
}
function initFontSize() {
    let pref_font_size = userpref.getUserPref("gui_pref", "font_size");
    if (pref_font_size == undefined) {
        pref_font_size = 14;
    }
    $("#font-size").val(pref_font_size);
    $("#font-size").on("change", changeFontSize);
    $("#font-size").trigger("change");
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
function autosaveDelaySet() {
    let $this = $(this);
    let value = parseInt($this.val());
    if (
        !isNaN(value) &&
        value >= $this.attr("min") &&
        value <= $this.attr("max")
    ) {
        userpref.setUserPref("gui_pref", "autosave_delay", value);
        AUTOSAVE_DELAY = value;
    }
}
function initAutosave() {
    setInterval(autoSave, 100);
    let delay = userpref.getUserPref("gui_pref", "autosave_delay");
    if (delay == undefined) {
        delay = 1000;
    }
    AUTOSAVE_DELAY = delay;
    $("#autosave-delay").val(delay);
    $("#autosave-delay").on("change", autosaveDelaySet);
    $("#autosave-delay").trigger("change");
}
function initGUI() {
    loadThemes();
    $("#theme-select").on("change", selectTheme);
    initFontSize();
    initAutosave();
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
$(initGUI);
