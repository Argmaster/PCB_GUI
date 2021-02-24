
class ModelPackage {
    constructor(package_path, templates) {
        this.package_path = package_path;
        this.dec_path = `${package_path}/__dec__.json`;
        this.prm_path = `${package_path}/__prm__.json`;
        this.top_path = `${package_path}/__top__.png`;
        this.bot_path = `${package_path}/__bot__.png`;
        this.dec_dict = JSON.parse(fs.readFileSync(this.dec_path));
        this._class = this.dec_dict["class"];
        this.template = templates[this._class];
        if (this.template == undefined) {
            throw `Class ${this._class} is not available.`;
        }
        this._model = this.dec_dict.model;
        this._author = this.dec_dict.author;
        this._dscp = this.dec_dict.dscp;
        this._other = this.dec_dict.other;
        this.prm_dict = JSON.parse(fs.readFileSync(this.prm_path));
    }
    params() {
        return this.prm_dict;
    }
    async makeIcons() {
        let blender_io = new BlenderIO(userpref);
        await blender_io.begin();
        try {
            await blender_io.call(
                new IO_OUT("makeBotIcon", {
                    template_path: this.template.package_path,
                    template_params: this.params(),
                    model_path: this.package_path,
                })
            );
        } finally {
            blender_io.kill();
        }
    }
}
