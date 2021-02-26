class TemplatePackage {
    constructor(package_path) {
        this.package_path = package_path;
        this.pkg_path = `${package_path}/__pkg__`;
        this.gen_path = `${package_path}/__gen__`;
        this.pkg_dict = JSON.parse(fs.readFileSync(this.pkg_path));
        this._class = this.pkg_dict["class"];
        this._gtype = this.pkg_dict.gtype;
        this._author = this.pkg_dict.author;
        this._dscp = this.pkg_dict.dscp;
        this.tem_dict = this.pkg_dict.tem_dict;
    }
}
