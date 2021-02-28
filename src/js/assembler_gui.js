$(function () {
    $(".assembler-subsection-header").on("click", function () {
        let $this = $(this);
        let $body = $this.next();
        if ($body.is(":hidden")) {
            $body.show();
            $this.find("div").css({ transform: "rotate(0deg)" });
        } else {
            $body.hide();
            $this.find("div").css({transform: 'rotate(90deg)'});
        }
    });
});
