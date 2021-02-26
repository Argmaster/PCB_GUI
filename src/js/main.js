const { app, BrowserWindow, Menu, globalShortcut } = require("electron");
const { event } = require("jquery");
const os = require("os");
const path = require("path");

const createWindow = async () => {
    // Create the browser window.
    const mainWindow = new BrowserWindow({
        width: 1280,
        height: 720,
        minWidth: 960,
        minHeight: 540,
        titleBarStyle: "hidden",
        frame: false,
        backgroundColor: "#2e353b",
        webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true,
        },
    });

    window = await mainWindow.loadFile(
        path.join(__dirname, "../html/index.html")
    );
    await globalShortcut.register("Escape", () => mainWindow.close());
    await globalShortcut.register("Ctrl+R", () => mainWindow.reload());
    //mainWindow.webContents.openDevTools();
    mainWindow.setMenu(null);
};
app.on("ready", function () {
    createWindow();
});
app.on("window-all-closed", () => {
    app.quit();
});
app.on("activate", () => {
    createWindow();
});
