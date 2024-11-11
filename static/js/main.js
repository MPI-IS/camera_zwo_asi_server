$(document).ready(function() {
    // Function to load images initially and after capture
    function loadImages() {
        $.ajax({
            url: '/images', // Use a dedicated endpoint for fetching images
            method: 'GET',
            success: function(data) {
                if (data.images_info) {
                    $('#thumbnails tbody').empty(); // Clear existing thumbnails
                    data.images_info.forEach(function(image) {
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

                            const highResImg = $('<img>').attr('src', '/media/' + image.image_filename).attr('alt', 'High Resolution').addClass('img-fluid high-res');
                            highResColumn.append(highResImg);
                        }

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
                } else {
                    console.error("No images_info found in response");
                }
            }
        });
    }

    $('form').on('submit', function(event) {
        event.preventDefault();
        $.ajax({
            url: '/capture',
            method: 'POST',
            data: $(this).serialize(),
            success: function() {
                loadImages(); // Reload images after capture
            }
        });
    });

    function addHoverEffect() {
        $('.thumbnail img').hover(function() {
            const thumbnail = $(this);
            const highResContainer = thumbnail.closest('tr').find('.high-res-container');
            highResContainer.find('img').show(); // Show the high-resolution image
        }, function() {
            const thumbnail = $(this);
            const highResContainer = thumbnail.closest('tr').find('.high-res-container');
            highResContainer.find('img').hide(); // Hide the high-resolution image
        });
    }

    loadImages(); // Initial load of images
});
