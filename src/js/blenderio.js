const child_process = require("child_process");

class BlenderIO {
    constructor(script = "./src/py/loader.py") {
        this.blender_process = child_process.spawn(
            blender_executable,
            ["-b", "-P", script],
            {
                cwd: process.cwd(),
            }
        );
    }
    kill() {
        this.blender_process.kill();
    }
    async begin() {
        var mess = await this.read();
        while (mess.status != "READY") {
            mess = await this.read();
        }
    }
    read() {
        return new Promise(resolve => {
            if (this.blender_process.stdout.listenerCount("data") == 0)
                this.blender_process.stdout.on("data", data => {
                    let block = data.toString().trim().split("\n");
                    for (data of block) {
                        try {
                            data = JSON.parse(data);
                            this.blender_process.stdout.removeAllListeners();
                            resolve(data);
                        } catch (e) {
                        }
                    }
                });
        });
    }
    write(data) {
        this.blender_process.stdin.write(JSON.stringify(data) + "\n");
    }
    async call(call_data) {
        this.write(call_data);
        let response = await this.read();
        if (response.status == "ERROR") throw Error(response.trace);
        return response;
    }
}
exports.BlenderIO = BlenderIO;
exports.BlenderIO();