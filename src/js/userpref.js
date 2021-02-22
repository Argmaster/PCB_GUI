const fs = require("fs");

class UserPref {
    constructor(pref_path = "./data/user/.pref") {
        this.pref = {};
        this.pref_path = pref_path;
        this.modified = true;
        this.load();
        this.log_change = this.getUserPref("debug", "log-user-pref", true);
    }
    setModelProp(model, prop, value) {
        if (this.pref.models == undefined) {
            this.pref.models = {};
        }
        if (this.pref.models[model] == undefined) {
            this.pref.models[model] = {};
        }
        this.pref.models[model][prop] = value;
        if (this.log_change)
            console.log(`UserPref Model: ${model}{} -> ${prop} = ${value}`);
        this.modified = true;
    }
    delModelProp(model, prop) {
        if (this.pref.models == undefined) {
            this.modified = true;
            this.pref.models = {};
            return;
        }
        if (this.pref.models[model] != undefined) {
            this.modified = true;
            delete this.pref.models[model][prop];
            if (this.log_change)
                console.log(`UserPref Model: ${model}{} -> delete ${prop}`);
        } else {
            return;
        }
        if (Object.keys(this.pref.models[model]).length == 0) {
            this.modified = true;
            delete this.pref.models[model];
            if (this.log_change)
                console.log(`UserPref Model: delete ${model}{}`);
        }
    }
    getModelProp(model, prop) {
        if (this.pref.models == undefined) {
            this.pref.models = {};
            this.modified = true;
        }
        if (this.pref.models[model] == undefined) {
            return undefined;
        }
        return this.pref.models[model][prop];
    }
    setUserPref(prefdict, prop, value) {
        if (this.pref[prefdict] == undefined) {
            this.pref[prefdict] = {};
        }
        if (this.pref[prefdict][prop] != value) {
            this.pref[prefdict][prop] = value;
            if (this.log_change)
                console.log(`UserPref: ${prefdict}{} -> ${prop} = ${value}`);
            this.modified = true;
        }
    }
    getUserPref(prefdict, prop, _default) {
        if (this.pref[prefdict] == undefined) {
            this.pref[prefdict] = {};
        }
        if (this.pref[prefdict][prop] == undefined) return _default;
        else return this.pref[prefdict][prop];
    }
    delUserPref(prefdict, prop) {
        if (this.pref[prefdict] == undefined) {
            this.pref[prefdict] = {};
        } else if (this.pref[prefdict][prop] != undefined) {
            delete this.pref[prefdict][prop];
            this.modified = true;
        }
    }
    load() {
        try {
            this.pref = JSON.parse(fs.readFileSync(this.pref_path));
        } catch (e) {
            this.modified = true;
            this.save();
        }
    }
    save() {
        if (this.modified) {
            this.modified = false;
            fs.writeFileSync(this.pref_path, JSON.stringify(this.pref));
        }
    }
}
exports.UserPref = UserPref;

exports.saveSimpleProp = function (userpref, model, self) {
    let $this = $(self);
    if ($this.hasClass("text-input-mistake")) return;
    let key = $this.attr("param_id");
    let value = $this.val().trim();
    let _default = $this.attr("default");
    if (value.length && value != _default) {
        if (value != userpref.getModelProp(model._model, key))
            userpref.setModelProp(model._model, key, value);
    } else {
        userpref.delModelProp(model._model, key);
    }
};
exports.savePinrootPtr = function (userpref, model, self) {
    let $this = $(self);
    let key = "$__" + $this.attr("id");
    let value = $this.val().trim();
    if (value.length && value != 0) {
        if (value != userpref.getModelProp(model._model, key))
            userpref.setModelProp(model._model, key, value);
    } else {
        userpref.delModelProp(model._model, key);
    }
};
