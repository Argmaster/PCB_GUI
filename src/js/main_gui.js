const fs = require("fs");
const {
    dialog,
    getCurrentWebContents,
    app,
    BrowserWindow,
} = require("electron").remote;
const currentWebContents = getCurrentWebContents();
const mainWindow = BrowserWindow.getFocusedWindow();

const UserPref = require("../js/userpref").UserPref;
const userpref = new UserPref();

function makeDataDirs() {
    if (!fs.existsSync("./blender/blender.exe")) {
        dialog.showErrorBox(
            "blender.exe not found.",
            "Unable to find blender executable, exiting."
        );
        let w = remote.getCurrentWindow();
        w.close();
    }
    try {
        if (fs.existsSync("./temp")) {
            fs.rmdirSync("./temp", { recursive: true });
        }
        fs.mkdirSync("./temp");
        fs.mkdirSync("./temp/gerber");
    } catch (e) {}
    try {
        fs.mkdirSync("./data");
    } catch (e) {}
    try {
        fs.mkdirSync("./data/user");
    } catch (e) {}
    try {
        fs.mkdirSync("./data/assets");
    } catch (e) {}
    try {
        fs.mkdirSync("./data/assets/models");
    } catch (e) {}
    try {
        fs.mkdirSync("./data/assets/templates");
    } catch (e) {}
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
function initWindowNav() {
    $("#window-window-buttons :nth-child(1)").on("click", () => {
        mainWindow.minimize();
    });
    $("#window-window-buttons :nth-child(2)").on("click", () => {
        if (!mainWindow.isMaximized()) mainWindow.maximize();
        else mainWindow.restore();
    });
    $("#window-window-buttons :nth-child(3)").on("click", () => {
        mainWindow.close();
    });
}
function initWindowGUI() {
    initWindowNav();
    initBookmarks();
}
makeDataDirs();
$(initWindowGUI);
