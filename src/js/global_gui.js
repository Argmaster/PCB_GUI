globalWorkspaceAdd = {
    box: function () {
        $("#global-settings-box").append(
            `<div class="global-content-box"></div>`
        );
    },
    title: function (title) {
        $(".global-content-box")
            .last()
            .append(`<div class="global-row-title">${title}</div>`);
    },
    subtitle: function (title) {
        $(".global-content-box")
            .last()
            .append(`<div class="global-content-label">${title}</div>`);
    },
    entrySelect: function (label, options, _default, RNA, userpref, _callback) {
        let options_html = "";
        for (let opt of options) {
            options_html += `<option value="${opt[0]}">${opt[1]}</option>`;
        }
        $(".global-content-box").last().append(
            `<div class="global-row">
                <div class="global-half-row">
                    <div class="global-content-label">${label}</div>
                </div>
                <div class="global-half-row">
                    <select class="standard-text-input" RNA="${RNA}">${options_html}</select>
                </div>
            </div>`
        );
        let $this = $(`select[RNA="${RNA}"]`);
        $this.val(
            userpref.pref[RNA] == undefined ? _default : userpref.pref[RNA]
        );
        $this.on("change", function () {
            let $this = $(`select[RNA="${RNA}"]`);
            userpref.set(RNA, $this.val());
            if (_callback != undefined) {
                _callback($this);
            }
        });
        $this.trigger("change");
    },
    entryNumber: function (
        label,
        max,
        min,
        step,
        _default,
        suffix,
        RNA,
        userpref,
        _callback
    ) {
        $(".global-content-box").last().append(
            `<div class="global-row">
                <div class="global-half-row">
                    <div class="global-content-label">${label}</div>
                </div>
                <div class="global-half-row">
                    <input
                        type="text"
                        value="${_default}"
                        class="standard-text-input"
                        RNA="${RNA}"
                        placeholder="${_default}"
                    />
                    ${suffix}
                </div>
            </div>`
        );
        let $this = $(`input[RNA="${RNA}"]`);
        $this.val(
            userpref.pref[RNA] == undefined ? _default : userpref.pref[RNA]
        );
        let f;
        if (step != 1) {
            f = parseInt;
        } else {
            f = parseFloat;
        }
        $this.on("input", function () {
            let $this = $(`input[RNA="${RNA}"]`);
            let value = f($this.val());
            if (!isNaN(value) && value >= min && value <= max) {
                $this.removeClass("text-input-mistake");
                $this.val(value);
                userpref.set(RNA, $this.val());
                if (_callback != undefined) {
                    _callback($this);
                }
            } else {
                $this.addClass("text-input-mistake");
            }
        });
        $this.trigger("input");
    },
    entryToggle: function (label, _default, RNA, userpref, _callback) {
        $(".global-content-box").last().append(
            `<div class="global-row">
            <div class="global-half-row">
                <div class="global-content-label">
                    ${label}
                </div>
            </div>
            <div class="global-half-row">
                <label class="switch">
                    <input
                        type="checkbox"
                        RNA="${RNA}"
                    />
                    <span class="slider round"></span>
                </label>
            </div>
        </div>`
        );
        let $this = $(`input[RNA="${RNA}"]`);
        $this.attr(
            "checked",
            userpref.pref[RNA] == undefined ? _default : userpref.pref[RNA]
        );
        $this.on("input", function () {
            let $this = $(`input[RNA="${RNA}"]`);
            userpref.set(RNA, $this.prop("checked"));
            if (_callback != undefined) {
                _callback($this);
            }
        });
        $this.trigger("input");
    },
    entryClick: function (label, button_label, _callback) {
        $(".global-content-box").last().append(
            `<div class="global-row">
            <div class="global-half-row">
                <div class="global-content-label">
                    ${label}
                </div>
            </div>
            <div class="global-half-row">
                <input
                    type="button"
                    value="${button_label}"
                    class="standard-text-input"
                />
            </div>
        </div>`
        );
        let $this = $(".global-content-box").last().find(".global-row").last();
        $this.on("click", function () {
            _callback($this);
        });
    },
};
