const { app, BrowserWindow, Menu } = require("electron");
const os = require("os");
const path = require("path");

const createWindow = async () => {
    // Create the browser window.
    const mainWindow = new BrowserWindow({
        width: 1000,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true,
        },
    });

    window = await mainWindow.loadFile(
        path.join(__dirname, "../html/index.html")
    );
    mainWindow.webContents.openDevTools();
    //mainWindow.setMenu(null);
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
