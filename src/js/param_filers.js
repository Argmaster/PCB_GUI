function ok(thing) {
    thing.removeClass("text-input-mistake");
    thing.addClass("text-input-changed");
}
function err(thing) {
    thing.removeClass("text-input-changed");
    thing.addClass("text-input-mistake");
}
function clear(thing) {
    thing.removeClass("text-input-changed");
    thing.removeClass("text-input-mistake");
}
exports.parseUnitOfLength = function (value) {
    let float_re = "[\\-+]?\\d*\\.?\\d+";
    if (value.match(`${float_re}mils$|${float_re}mil$`)) {
        return parseFloat(value.replace(/mils|mil/, "")) * 2.54 * 1e-5;
    } else if (value.match(`${float_re}inch$|${float_re}in$`)) {
        return parseFloat(value.replace(/inch|in/, "")) * 0.0254;
    } else if (value.match(`${float_re}ft$`)) {
        return parseFloat(value.replace(/ft/, "")) * 0.3048;
    } else if (value.match(`${float_re}mm$`)) {
        return parseFloat(value.replace(/mm/, "")) * 0.001;
    } else if (value.match(`${float_re}cm$`)) {
        return parseFloat(value.replace(/cm/, "")) * 0.01;
    } else if (value.match(`${float_re}dm$`)) {
        return parseFloat(value.replace(/dm/, "")) * 0.1;
    } else if (value.match(`${float_re}m$`)) {
        return parseFloat(value.replace(/m/, ""));
    } else if (value.match(`${float_re}$`)) {
        return parseFloat(value);
    } else {
        return NaN;
    }
};
exports.UnitOfLength = function () {
    let $this = $(this);
    let value = $this.val();
    let _default = $this.attr("default");
    if (value && value != _default) {
        if (isNaN(exports.parseUnitOfLength(value))) {
            err($this);
        } else {
            ok($this);
        }
    } else {
        clear($this);
    }
};
exports.Int = function () {
    let $this = $(this);
    let max = parseFloat($this.attr("max"));
    let min = parseFloat($this.attr("min"));
    let inclusive = $this.attr("inclusive") == "true";
    let value = $this.val();
    let _default = $this.attr("default");
    if (value && value != _default) {
        value = parseInt(value);
        if (inclusive) {
            if (isNaN(value) || value > max || value < min) {
                err($this);
            } else {
                ok($this);
            }
        } else {
            if (isNaN(value) || value >= max || value <= min) {
                err($this);
            } else {
                ok($this);
            }
        }
    } else {
        clear($this);
    }
};
exports.Float = function () {
    let $this = $(this);
    let max = parseFloat($this.attr("max"));
    let min = parseFloat($this.attr("min"));
    let inclusive = $this.attr("inclusive") == "true";
    let value = $this.val();
    let _default = $this.attr("default");
    if (value && value != _default) {
        value = parseFloat(value);
        if (inclusive) {
            if (isNaN(value) || value > max || value < min) {
                err($this);
            } else {
                ok($this);
            }
        } else {
            if (isNaN(value) || value >= max || value <= min) {
                err($this);
            } else {
                ok($this);
            }
        }
    } else {
        clear($this);
    }
};
exports.String = function () {
    let $this = $(this);
    let value = $this.val();
    if (value && value != $this.attr("default")) {
        ok($this);
    } else {
        clear($this);
    }
};
