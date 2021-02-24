const clamp = (num, min, max) => Math.min(Math.max(num, min), max);
let _float_regex = `^[\\-+]?[0-9]*\\.?[0-9]+`;
let _angle_regex = [
    [`${_float_regex}rad`, /mil/, 1],
    [`${_float_regex}deg`, /deg/, Math.PI / 180],
    [`${_float_regex}°`, /°/, Math.PI / 180],
    [`${_float_regex}'`, /'/, Math.PI / 10800],
    [`${_float_regex}"`, /'/, Math.PI / 648000],
    [`${_float_regex}turn`, /turn/, Math.PI],
];
let _unitoflength_regex = [
    [`${_float_regex}mil`, /mil/, 2.54 * 1e-5],
    [`${_float_regex}in`, /in/, 0.0254],
    [`${_float_regex}ft`, /ft/, 0.3048],
    [`${_float_regex}mm`, /mm/, 0.001],
    [`${_float_regex}cm`, /cm/, 0.01],
    [`${_float_regex}dm`, /dm/, 0.1],
    [`${_float_regex}m`, /m/, 1],
    [`${_float_regex}`, "", 1],
];
let TType = {
    _destruct_literal(literal, literal_regex) {
        let value = 0;
        literal = literal.trim();
        while (literal.length) {
            literal = literal.trim();
            let no_match = true;
            for (let [regex, repl, multiplier] of literal_regex) {
                let regex_match = literal.match(regex);
                if (regex_match != null) {
                    let literal_match = regex_match[0];
                    literal = literal.substr(
                        regex_match.index + literal_match.length
                    );
                    literal_match = parseFloat(literal_match.replace(repl, ""));
                    value += literal_match * multiplier;
                    no_match = false;
                    break;
                }
            }
            if (no_match) return NaN;
        }
        return value;
    },
    _color_rgb: function (literal = "") {
        /**
         * Convert rgba(R, G, B) color literal to number[4] array, alpha 255
         * @param {string} literal to parse
         * @returns {number[4]} array of 4 numbers in range 0 - 255
         * @type {number[4]}
         */
        literal = literal.replace(/rgb\(/, "").replace(/\)/, "").split(/,/);
        literal.forEach((e, i, a) => (a[i] = clamp(parseInt(e), 0, 255)));
        literal.push(255);
        return literal;
    },
    _color_rgba: function (literal = "") {
        /**
         * Convert rgba(R, G, B, A) color literal to number[4] array
         * @param {string} literal to parse
         * @returns {number[4]} array of 4 numbers in range 0 - 255
         * @type {number[4]}
         */
        literal = literal
            .replace(/rgba\(/, "")
            .replace(/\)/, "")
            .split(/,/);
        literal.forEach((e, i, a) => (a[i] = clamp(parseInt(e), 0, 255)));
        return literal;
    },
    _number_rgba: function (_number) {
        /**
         * Convert number 0x0 - 0xFFFFFFFF to array RGBA {number[4]}
         * @param {number} _number to parse
         * @returns {number[4]} array of 4 numbers in range 0 - 255
         * @type {number[4]}
         */
        let value = [0, 0, 0, 255];
        for (let i = 0; i < 4; i++) {
            value[3 - i] = _number % 256;
            _number = Math.floor(_number / 256);
        }
        return value;
    },
    Color: function (literal = "") {
        /**
         * Parse a color literal in one of following forms:
         * number:
         *  0x0 - 0xFFFFFFFF as RRGGBBAA
         * string:
         *  "0xFFFFFFFF" - "0x00000000" RRGGBBAA
         *   "#FFFFFFFF" - "#00000000"  RRGGBBAA
         *    "0xFFFFFF" - "0x000000"   RRGGBB alpha 255
         *     "#FFFFFF" - "#000000"    RRGGBB alpha 255
         *      "0xFFFF" - "0x0000"     RGBA, -> #ABCD = #AABBCCDD
         *       "#FFFF" - "#0000"      RGBA, as above
         *       "0xFFF" - "0x000"      RGB alpha 255 -> #ABC = #AABBCC
         *        "#FFF" - "#000"       RGB alpha 255, as above
         *  "rgba(255, 255, 255, 255)" - "rgb(0, 0, 0, 0)"  RGBA
         *        "rgb(255, 255, 255)" - "rgb(0, 0, 0)"     RGB alpha 255
         *
         * @param {string|number} literal literal to resolve
         * @returns {number[4]} color array [R, G, B, A]
         * @type {number[4]}
         * @type {NaN} if value cannot be parsed
         */
        // parse string literals
        if (typeof literal == "string") {
            literal = literal.trim();
            // rgb(R, G, B) literal
            if (
                literal.match(
                    /rgb\(\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*\)/
                )
            )
                return this._color_rgb(literal);
            // rgba(R, G, B, A) literal
            else if (
                literal.match(
                    /rgba\(\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*\)/
                )
            )
                return this._color_rgba(literal);
            // 0xFFFFFFFF or #FFFFFFFF literal
            else if (literal.match(/[#(0x)][0-9A-Fa-f]{8}/))
                return this._number_rgba(parseInt(literal.replace("#", "0x")));
            // 0xFFFFFF or #FFFFFF literal
            else if (literal.match(/[#(0x)][0-9A-Fa-f]{6}/))
                return this._number_rgba(
                    parseInt((literal + "FF").replace("#", "0x"))
                );
            else if (literal.match(/[#(0x)][0-9A-Fa-f]{4}/)) {
                // 0xFFFF or #FFFF literal
                literal = literal.replace(/#|0x/, "");
                let _literal = [0, 0, 0, 0];
                _literal.forEach(
                    (_, i, a) =>
                        (a[i] = parseInt(`0x${literal[i]}${literal[i]}`))
                );
                return _literal;
            } else if (literal.match(/[#(0x)][0-9A-Fa-f]{3}/)) {
                // 0xFFF or #FFF literal
                literal = literal.replace(/#|0x/, "");
                let _literal = [0, 0, 0];
                _literal.forEach(
                    (_, i, a) =>
                        (a[i] = parseInt(`0x${literal[i]}${literal[i]}`))
                );
                _literal.push(255);
                return _literal;
            }
        } else if (typeof literal == "number") {
            // number literal, values 0 - 4294967295 0x0 - 0xFFFFFFFF
            return this._number_rgba(literal);
        }
        return NaN;
    },
    Angle: function (literal = "") {
        if (typeof literal == "string") {
            return this._destruct_literal(literal, _angle_regex);
        } else {
            return parseFloat(literal);
        }
    },
    UnitOfLength: function (literal = "") {
        if (typeof literal == "string") {
            return this._destruct_literal(literal, _unitoflength_regex);
        } else {
            return parseFloat(literal);
        }
    },
};
