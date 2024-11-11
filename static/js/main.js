$(document).ready(function() {
    $('form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            url: '/capture',
            method: 'POST',
            data: $(this).serialize(),
            success: function(data) {
                data.forEach(function(image) {
                    $('#thumbnails').append(
                        '<div class="thumbnail">' +
                        '<a href="/media/' + image.image_filename + '">' +
                        '<img src="/media/' + image.thumbnail_filename + '" alt="Thumbnail">' +
                        '</a>' +
                        '<div class="config">Exposure: ' + image.config.exposure + ', Gain: ' + image.config.gain + ', Focus: ' + image.config.focus + ', Aperture: ' + image.config.aperture + '</div>' +
                        '</div>'
                    );
                });
                addHoverEffect();
            }
        });
    });

    function addHoverEffect() {
        $('.thumbnail img').hover(function(event) {
            const thumbnail = $(this);
            const highResImg = $('<div class="high-res"><img src="/media/' + thumbnail.parent().attr('href').split('/').pop() + '"></div>');
            thumbnail.parent().append(highResImg);
            highResImg.fadeIn();

            thumbnail.on('mousemove', function(e) {
                const offset = thumbnail.offset();
                const x = e.pageX - offset.left;
                const y = e.pageY - offset.top;
                const img = highResImg.find('img');
                const scale = img.width() / thumbnail.width();
                img.css({
                    left: -x * scale + highResImg.width() / 2,
                    top: -y * scale + highResImg.height() / 2
                });
            });
        }, function() {
            $(this).siblings('.high-res').remove();
        });
    }

    addHoverEffect();
});
