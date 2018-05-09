var gallery = document.getElementById('gallery');

function scale_gallery () {
    var galleryContainer = document.getElementById('gallery-container');
    var html = document.getElementsByTagName('html')[0];
    var galleryContainerWidth = parseInt(galleryContainer.clientWidth);
    var columnCount = Math.floor(galleryContainerWidth / (parseInt(250) + 14));
    var newGalleryWidth =  (parseInt(250) + 14) * columnCount;
    html.style.setProperty("--gallery-width", newGalleryWidth);
    html.style.setProperty("--square-size", 250);
}

gallery.onload = scale_gallery();
