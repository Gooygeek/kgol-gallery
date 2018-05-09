var slider = document.getElementById("myRange");
var output = document.getElementById("slider-value");
var html = document.getElementsByTagName('html')[0];
var galleryContainer = document.getElementById('gallery-container')
var galleryContainerWidth = parseInt(galleryContainer.clientWidth);

slider.oninput = function() {
    galleryContainerWidth = parseInt(galleryContainer.clientWidth);
    var columnCount = Math.floor(galleryContainerWidth / (parseInt(this.value) + 14));
    var newGalleryWidth =  (parseInt(this.value) + 14) * columnCount;
    html.style.setProperty("--gallery-width", newGalleryWidth);
    html.style.setProperty("--square-size", this.value);
}

window.onresize = function () {
    galleryContainerWidth = parseInt(galleryContainer.clientWidth);
    var columnCount = Math.floor(galleryContainerWidth / (parseInt(slider.value) + 14));
    var newGalleryWidth =  (parseInt(slider.value) + 14) * columnCount;
    html.style.setProperty("--gallery-width", newGalleryWidth);
    html.style.setProperty("--square-size", slider.value);
}
