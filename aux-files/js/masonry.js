
(function () {
    var slider = document.getElementById("myRange");
    var html = document.getElementsByTagName('html')[0];
    slider.addEventListener("input", slider_input);

    function slider_input() {
        resize();
        html.style.setProperty("--square-size", this.value);
    }

    var item = document.getElementById('item');

    window.addEventListener("resize", window_resize);

    function window_resize() {
        resize();
        const itemWidth = getStyleValue(item, 'width');
        console.log(itemWidth);
        slider.value = itemWidth;
    }

    var gallery = document.getElementById("Gallery");
    var galleryLoading = document.getElementById("gallery-loading");
    window.addEventListener("load", window_load);

    function window_load() {
        gallery.style.setProperty('display', 'block');
        galleryLoading.style.setProperty('display', 'none');
        resize();
    }

    function resize() {
        const grid = document.querySelector(".grid");
        const rowHeight = getStyleValue(grid, "grid-auto-rows");
        const rowGap = getStyleValue(grid, "grid-row-gap");
        grid.style.gridAutoRows = "auto";
        grid.style.alignItems = "self-start";
        grid.querySelectorAll(".item").forEach(item => {
            item.style.gridRowEnd = `span ${Math.ceil(
                (item.clientHeight + rowGap) / (rowHeight + rowGap)
            )}`;
        });
        grid.removeAttribute("style");
    }

    function getStyleValue(element, style) {
        return parseInt(window.getComputedStyle(element).getPropertyValue(style));
    }

})();

function addPTag (tagName) {
    console.log("adding pTag: "+ tagName);
}

function addNTag (tagName) {
    console.log("adding nTag: "+ tagName);
}