const fs = require("fs");
const tar = require("tar");
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
        fs.mkdirSync("./temp/gerber", { recursive: true });
    } catch (e) {}
    try {
        fs.mkdirSync("./data/assets/templates", { recursive: true });
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
String.prototype.hashCode = function () {
    var hash = 0;

    if (this.length == 0) return hash;

    for (i = 0; i < this.length; i++) {
        char = this.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash;
    }

    return hash;
};
function disableComponent(target) {
    if (!$(target).attr("disabled")) {
        $(target).attr("disabled", true);
        $(target).css("cursor", "wait");
        $(target).css("filter", "saturate(50%)");
        return true;
    } else {
        return false;
    }
}
function enableComponent(target) {
    $(target).attr("disabled", false);
    $(target).css("cursor", "pointer");
    $(target).css("filter", "saturate(100%)");
}
function showErrorBox(message, error) {
    if (userpref.get("debug.log.javascript.stack"))
        dialog.showErrorBox(message, error.stack);
    else dialog.showErrorBox(message, error.message);
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
