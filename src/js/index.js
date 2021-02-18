$(".bookmark-box").each(function (index) {
    $(this).attr("id", `bk${index}`);
    $(this).on("click", () => toggleBookmark(index));
});
$(".workspace-box").each(function (index) {
    $(this).attr("id", `ws${index}`);
});
function toggleBookmark(index) {
    const bookmark = $(`#bk${index}`);
    if (!bookmark.hasClass("bookmark-active")) {
        // togle bookmark highlight
        $(".bookmark-active").each(function () {
            $(this).addClass("bookmark-inactive");
            $(this).removeClass("bookmark-active");
        });
        bookmark.addClass("bookmark-active");
        bookmark.removeClass("bookmark-inactive");
        // show workspace
        $(".workspace-box").each(function () {
            $(this).hide();
        });
        var workspace = $(`#ws${index}`);
        workspace.show();
    }
}
toggleBookmark(0);
