$(document).ready(function() {
    $('form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            url: '/capture',
            method: 'POST',
            data: $(this).serialize(),
            success: function(data) {
                $('#thumbnails tbody').empty(); // Clear existing thumbnails
                data.forEach(function(image) {
                    const row = $('<tr></tr>');
                    const thumbnailColumn = $('<td class="align-middle"></td>');
                    const highResColumn = $('<td class="align-middle high-res-container"></td>');
                    const configColumn = $('<td class="align-middle"></td>');

                    if (image.error) {
                        thumbnailColumn.append('<div class="alert alert-danger">' + image.error + '</div>');
                    } else {
                        const thumbnail = $('<div class="thumbnail"></div>');
                        const link = $('<a></a>').attr('href', '/media/' + image.image_filename);
                        const img = $('<img>').attr('src', '/media/' + image.thumbnail_filename).attr('alt', 'Thumbnail').addClass('img-fluid');
                        link.append(img);
                        thumbnail.append(link);
                        thumbnailColumn.append(thumbnail);
                    }

                    // Use let instead of const for configInfo
                    let configInfo = 'Exposure: ' + image.config.exposure + ', Gain: ' + image.config.gain;
                    if (image.config.focus !== null) {
                        configInfo += ', Focus: ' + image.config.focus;
                    }
                    if (image.config.aperture !== null) {
                        configInfo += ', Aperture: ' + image.config.aperture;
                    }
                    configColumn.append('<div class="config">' + configInfo + '</div>');

                    row.append(thumbnailColumn);
                    row.append(highResColumn);
                    row.append(configColumn);
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
            const highResContainer = thumbnail.closest('tr').find('.high-res-container');
            highResContainer.append(highResImg);
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
            $(this).closest('tr').find('.high-res-container .high-res').remove();
        });
    }

    addHoverEffect();
});
