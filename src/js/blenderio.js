const child_process = require("child_process");

class BlenderIO {
    constructor(script = "./src/py/loader.py") {
        this.blender_process = child_process.spawn(
            blender_executable,
            ["--log-level", "100", "-b", "-P", script],
            {
                cwd: process.cwd(),
            }
        );
    }
    kill() {
        this.blender_process.kill();
    }
    async begin() {
        var mess = "";
        while (mess != "READY") {
            mess = await this.read();
        }
    }
    read() {
        return new Promise(resolve => {
            if (this.blender_process.stdout.listenerCount("data") == 0)
                this.blender_process.stdout.once("data", data => {
                    data = data.toString();
                    try {
                        resolve(JSON.parse(data));
                    } catch (e) {
                        resolve(data);
                    }
                });
        });
    }
    write(data) {
        this.blender_process.stdin.write(JSON.stringify(data) + "\n");
    }
    async sendCode(code) {
        this.write(code);
        let res = await this.read();
        if (res != "OK") throw new Error(`Invalid Response: ${res}`);
        return;
    }
}
exports.BlenderIO = BlenderIO;
