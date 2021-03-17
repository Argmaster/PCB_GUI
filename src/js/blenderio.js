const child_process = require("child_process");
const net = require("net");

class IO_IN {
    constructor(initializer) {
        this.status = initializer.status;
        this.data = initializer.data;
    }
}
exports.IO_IN = IO_IN;

class IO_OUT {
    constructor(status, data = null) {
        this.status = status;
        this.data = data;
    }
    json() {
        return JSON.stringify({ status: this.status, data: this.data }) + "\n";
    }
}
exports.IO_OUT = IO_OUT;

class BlenderIO {
    constructor(
        userpref,
        script = `./src/py/entry.py`,
        blender_executable = `${process.cwd()}\\blender\\blender.exe`,
    ) {
        this.js_log_in = userpref.get("debug.log.javascript.in");
        this.js_log_out = userpref.get("debug.log.javascript.out");
        this.python_log_in = userpref.get("debug.log.python.in");
        this.python_log_out = userpref.get("debug.log.python.out");
        this.blender_background = userpref.get("debug.blender.background");
        this.keep_blender_open = userpref.get("debug.blender.keep_open");
        this.render_engine = userpref.get("debug.blender.engine");
        this.render_samples = userpref.get("debug.blender.samples");
        this.render_dpi = userpref.get("debug.blender.dpi");
        this.STREAM_FIFO = [];
        this.SOCKET_FIFO = [];
        this.SOCKET_BUFF = "";
        this.socket_io = null;
        this.MODE = "STREAM";
        this.IPv4 = "127.0.0.1";
        this.PORT = null;

        let args = ["-P", script];
        if (this.blender_background) {
            args.unshift("-b");
        }
        this.blender_process = child_process.spawn(blender_executable, args, {
            cwd: process.cwd(),
        });
        this.stdout = this.blender_process.stdout;
        this.stdout.on("data", raw_data => {
            for (const sub_block of raw_data.toString().trim().split("\n")) {
                try {
                    this.STREAM_FIFO.push(JSON.parse(sub_block));
                } catch (e) {}
            }
        });
        this.stdin = this.blender_process.stdin;
    }
    kill() {
        if (!this.keep_blender_open) {
            this.blender_process.kill();
            this.socket_io.destroy();
        } else {
            this.call(new IO_OUT("Detach"));
        }
    }
    async begin() {
        let mess = await this.read_status("READY");
        this.MODE = "SOCKET";
        this.PORT = mess.data.port;
        this.socket_io = new net.Socket();
        await new Promise(resolve => {
            if (!this.socket_io.connecting) {
                this.socket_io.connect(this.PORT, this.IPv4, () => {
                    resolve(true);
                });
            }
        });
        this.socket_io.on("data", raw_data => {
            for (const sub_block of raw_data.toString().trim().split("\n")) {
                try {
                    this.SOCKET_FIFO.push(JSON.parse(sub_block));
                } catch (e) {}
            }
        });
        this.write(
            new IO_OUT("READY SOCKET", {
                python_log_in: this.python_log_in,
                python_log_out: this.python_log_out,
                render_engine: this.render_engine,
                render_samples: this.render_samples,
                render_dpi: this.render_dpi,
            })
        );
        mess = await this.read_status("WAITING SOCKET");
    }
    _read_source(fifo) {
        function pull(resolve) {
            if (fifo.length > 0) {
                resolve(new IO_IN(fifo.shift()));
            } else {
                setTimeout(() => pull(resolve), 10);
            }
        }
        return new Promise(resolve => {
            pull(resolve);
        });
    }
    async read() {
        let mess;
        if (this.MODE == "STREAM") {
            mess = await this._read_source(this.STREAM_FIFO);
        } else if (this.MODE == "SOCKET") {
            mess = await this._read_source(this.SOCKET_FIFO);
        }
        if (this.js_log_io) {
            console.log(mess);
        }
        return mess;
    }
    async read_status(status) {
        let mess = await this.read();
        if (mess.status != status) {
            throw Error(`BlenderIO connection error ${mess.data.trace}`);
        }
        return mess;
    }
    _write_stream(io_out_message) {
        this.stdin.write(io_out_message.json());
    }
    _write_socket(io_out_message) {
        this.socket_io.write(io_out_message.json());
    }
    write(io_out_message) {
        if (this.js_log_out) {
            console.log(io_out_message);
        }
        if (this.MODE == "STREAM") {
            this._write_stream(io_out_message);
        } else if (this.MODE == "SOCKET") {
            this._write_socket(io_out_message);
        }
    }
    async call(io_out_call, status_ok = "OK") {
        this.write(io_out_call);
        let mess = await this.read_status(status_ok);
        return mess;
    }
}
exports.BlenderIO = BlenderIO;
