//'require\((.*?\(.*?\))*\)'
class ModelPackage {
    constructor(package_path, templates) {
        this.package_path = package_path;
        this.dec_path = `${package_path}/__dec__.json`;
        this.top_path = `${package_path}/__top__.png`;
        this.bot_path = `${package_path}/__bot__.png`;
        this.mod_path = `${package_path}/__mod__.glb`;
        this.ico_path = `${package_path}/__ico__.png`;
        this.dec_dict = JSON.parse(fs.readFileSync(this.dec_path));
        this._class = this.dec_dict["class"];
        let regex = `[a-zA-Z0-9\\-_ \\.,\\(\\)\\[\\]\\{\\}:;\\*]`;
        if (this._class.match(`^${regex}{1,32}$`) == null) {
            throw Error(
                `Class name ${this._class} conatins forbidden signs or is too long.\nYou can use only use following sings: a-z A-Z 0-9 -_:;.,*()[]{} and space.\nIt's length have to be within 1 to 32.`
            );
        }
        this.template = templates[this._class];
        if (this.template == undefined) {
            throw `Class ${this._class} is not available.`;
        }
        this._model = this.dec_dict.model;
        if (this._model.match(`^${regex}{1,32}$`) == null) {
            throw Error(
                `Model name ${this._model} conatins forbidden signs or is too long.\nYou can use only use following sings: a-z A-Z 0-9 -_:;.,()[]{} and space.\nIt's length have to be within 1 to 32.`
            );
        }
        this._author = this.dec_dict.author;
        this._dscp = this.dec_dict.dscp;
        if (this._dscp.match(`^${regex}{0,512}$`) == null) {
            throw Error(
                `Model description conatins forbidden signs or is too long.\nYou can use only use following sings: a-z A-Z 0-9 -_:;.,()[]{} and space.\nIt's length have to be within 0 to 512.`
            );
        }
        this._other = this.dec_dict.other;
        this.prm_dict = this.dec_dict.prm_dict;
    }
    async makeModelAssets() {
        let blender_io = new BlenderIO(userpref);
        await blender_io.begin();
        try {
            await blender_io.call(
                new IO_OUT("makeModelAssets", {
                    template_params: this.traverse(),
                    model_path: this.package_path,
                }),
                "OK"
            );

        } finally {
            blender_io.kill();
        }
    }
    _traverse(structure, ttype, rna) {
        let out;
        switch (ttype) {
            case "UnitOfLength":
            case "Color":
            case "Angle":
            case "Float":
            case "Int":
            case "Keyword":
            case "Bool":
            case "ExistingFilePath":
            case "ExistingDirPath":
            case "PathExpression":
            case "String":
                out = userpref.getModelRNA(this._model, rna);
                return out == undefined ? RNAtoParam(this, rna) : out;
            case "MaterialParams":
                out = {};
                for (let key in MATERIAL_TEMPLATE)
                    out[key] = this._traverse(
                        MATERIAL_TEMPLATE[key],
                        MATERIAL_TEMPLATE[key].ttype,
                        rna.length > 0 ? `${rna}.${key}` : key
                    );
                return out;
            case "NestedTemplate":
                out = {};
                for (let key in structure.template)
                    out[key] = this._traverse(
                        structure.template[key],
                        structure.template[key].ttype,
                        rna.length > 0 ? `${rna}.${key}` : key
                    );
                return out;
            case "Vector":
                out = [];
                for (let key in structure.template)
                    out[key] = this._traverse(
                        structure.template[key],
                        structure.template[key].ttype,
                        rna.length > 0 ? `${rna}.${key}` : key
                    );
                return out;
            case "RAW":
                out = {};
                for (let key in structure)
                    out[key] = this._traverse(
                        structure[key],
                        structure[key].ttype,
                        rna.length > 0 ? `${rna}.${key}` : key
                    );
                return out;
            default:
                throw Error(
                    `Unable to traverse template for this model: ${ttype}; RNA: ${rna}`
                );
        }
    }
    traverse() {
        return this._traverse(this.template.tem_dict, "RAW", "");
    }
    async make(params, save_as_path) {
        let blender_io = new BlenderIO(userpref);
        await blender_io.begin();
        try {
            await blender_io.call(
                new IO_OUT("make3DModel", {
                    template_pkg_path: this.template.package_path,
                    template_params: params,
                    save_as: save_as_path,
                }),
                "OK"
            );
        } finally {
            blender_io.kill();
        }
    }
}
