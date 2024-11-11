$(document).ready(function() {
    $('form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            url: '/capture',
            method: 'POST',
            data: $(this).serialize(),
            success: function(data) {
                $('#thumbnails tbody').empty();
                data.forEach(function(image) {
                    const row = $('<tr></tr>');
                    const leftColumn = $('<td class="align-middle" style="width: 50%;"></td>');
                    const rightColumn = $('<td class="align-middle" style="width: 50%;"></td>');

                    if (image.error) {
                        leftColumn.append('<div class="alert alert-danger">' + image.error + '</div>');
                    } else {
                        const thumbnail = $('<div class="thumbnail"></div>');
                        const link = $('<a></a>').attr('href', '/media/' + image.image_filename);
                        const img = $('<img>').attr('src', '/media/' + image.thumbnail_filename).attr('alt', 'Thumbnail').addClass('img-fluid');
                        link.append(img);
                        thumbnail.append(link);
                        leftColumn.append(thumbnail);
                    }

                    const configInfo = 'Exposure: ' + image.config.exposure + ', Gain: ' + image.config.gain;
                    if (image.config.focus !== null) {
                        configInfo += ', Focus: ' + image.config.focus;
                    }
                    if (image.config.aperture !== null) {
                        configInfo += ', Aperture: ' + image.config.aperture;
                    }
                    rightColumn.append('<div class="config">' + configInfo + '</div>');

                    row.append(leftColumn);
                    row.append(rightColumn);
                    $('#thumbnails tbody').append(row);
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
