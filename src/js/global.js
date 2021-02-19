const themes = [];

function loadThemes() {
    for (const path of fs.readdirSync("./data/assets/themes").sort()) {
        $("#theme-select").append(`<option value="${path}">${path.split(".")[0]}</option>`);
    }
    let theme_pref = userpref.getUserPref("gui_pref", "theme");
    if (theme_pref == undefined) {
        theme_pref = "default.css";
    } $("#theme-select").val(theme_pref);
    selectTheme();
}
function selectTheme() {
    let theme_name = $("#theme-select").val();
    userpref.setUserPref("gui_pref", "theme", theme_name);
    $("#theme-style").attr("href", `../../data/assets/themes/${theme_name}`);

}
$("#theme-select").on("change", selectTheme);
$(loadThemes);
