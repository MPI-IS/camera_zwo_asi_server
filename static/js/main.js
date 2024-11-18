$(document).ready(function() {
    // Function to load images initially and after capture
    function loadImages() {
        $.ajax({
            url: '/images', // Use a dedicated endpoint for fetching images
            method: 'GET',
            success: function(data) {
                if (data.images_info) {
                    $('#thumbnails tbody').empty(); // Clear existing thumbnails
                    data.images_info.forEach(function(image, index) {
                        const row = $('<tr></tr>');
                        const thumbnailColumn = $('<td class="align-middle"></td>');
                        const highResColumn = $('<td class="align-middle high-res-container"></td>');
                        const configColumn = $('<td class="align-middle"></td>');
                        const downloadColumn = $('<td class="align-middle"></td>');
                        if (image.meta.error) {
                            // Display error message if present
                            thumbnailColumn.append('<div class="alert alert-danger">' + image.meta.error + '</div>');
                        } else if (image.meta.waiting) {
                            // Display "waiting for image" if image is waiting
                            thumbnailColumn.append('<div class="alert alert-info">waiting for image</div>');
                        } else {
                            const thumbnail = $('<div class="thumbnail"></div>');
                            const img = $('<img>').attr('src', '/media/' + image.thumbnail).attr('alt', 'Thumbnail').addClass('img-fluid').data('index', index);
                            thumbnail.append(img);
                            thumbnailColumn.append(thumbnail);

                            const highResImg = $('<img>').attr('src', '/media/' + image.image).attr('alt', 'High Resolution').addClass('img-fluid high-res');
                            highResColumn.append(highResImg);

                            const downloadLink = $('<a>').attr('href', '/media/' + image.image).attr('download', '').text('Download');
                            downloadColumn.append(downloadLink);
                        }

                        let configInfo = 'Exposure: ' + image.meta.exposure + '<br>Gain: ' + image.meta.gain;
                        if (image.meta.focus !== null) {
                            configInfo += '<br>Focus: ' + image.meta.focus;
                        }
                        if (image.meta.aperture !== null) {
                            configInfo += '<br>Aperture: ' + image.meta.aperture;
                        }
                        configColumn.append('<div class="config">' + configInfo + '</div>');
                        row.append(thumbnailColumn, highResColumn, configColumn, downloadColumn);
                        $('#thumbnails tbody').append(row);
                    });
                    addClickEffect();
                    restoreHighResImage();
                } else {
                    console.error("No images_info found in response");
                }
            }
        });
    }

    $('form').on('submit', function(event) {
        event.preventDefault();
        const captureButton = $(this).find('input[type="submit"]');
        captureButton.prop('disabled', true); // Disable the button

        $.ajax({
            url: '/capture',
            method: 'POST',
            data: $(this).serialize(),
            success: function() {
                loadImages(); // Reload images after capture
                setTimeout(() => {
                    captureButton.prop('disabled', false); // Re-enable the button after 1 second
                }, 1000);
            }
        });
    });

    function addClickEffect() {
        $('.thumbnail img').on('click', function(event) {
            const thumbnail = $(this);
            const index = thumbnail.data('index');

            // Calculate the position based on the click position
            const offset = thumbnail.offset();
            const x = event.pageX - offset.left;     // Get mouse x relative to the thumbnail
            const y = event.pageY - offset.top;      // Get mouse y relative to the thumbnail

            // Store the clicked position in local storage
            localStorage.setItem('clickPositionX', x);
            localStorage.setItem('clickPositionY', y);

            // Get the selected scale factor
            const scaleFactor = parseFloat($('#scale-factor').val());

            // Update all high-resolution images with the selected scale factor
            updateAllHighResImages(x, y, scaleFactor);
        });
    }

    function updateAllHighResImages(x, y, scaleFactor) {
        $('.thumbnail img').each(function() {
            const thumbnail = $(this);
            const fullResImgSrc = thumbnail.attr('src').replace('thumbnail_', '');

            // Create the high-resolution image element
            const highResImg = $('<img>')
                .attr('src', fullResImgSrc)
                .attr('alt', 'High Resolution')
                .addClass('high-res')
                .css({
                    'image-rendering': 'pixelated' // Disable smoothing
                });

            // Append the high-resolution image to the corresponding high-res container
            const highResContainer = thumbnail.closest('tr').find('.high-res-container');
            highResContainer.empty().append(highResImg);
            highResImg.show(); // Show the high-res image

            // Apply zoom using CSS transform
            highResImg.css({
                transform: `scale(${scaleFactor})`,
                transformOrigin: 'top left',
                position: 'absolute'
            });

            // Scale the position based on the high-res image and thumbnail size
            const scaleFactorX = highResImg.width() / thumbnail.width();
            const scaleFactorY = highResImg.height() / thumbnail.height();
            const newLeft = -(x * scaleFactorX * scaleFactor - (highResContainer.width() / 2));
            const newTop = -(y * scaleFactorY * scaleFactor - (highResContainer.height() / 2));

            // Set the high-res image position based on calculated positions
            highResImg.css({
                left: newLeft + 'px',
                top: newTop + 'px'
            });
        });
    }

    function restoreHighResImage() {
        const clickPositionX = localStorage.getItem('clickPositionX');
        const clickPositionY = localStorage.getItem('clickPositionY');
        const scaleFactor = parseFloat($('#scale-factor').val());

        if (clickPositionX !== null && clickPositionY !== null) {
            updateAllHighResImages(clickPositionX, clickPositionY, scaleFactor);
        }
    }

    function pollForNewImages() {
        setInterval(function() {
            loadImages(); // Reload images periodically
        }, 5000); // Poll every 5 seconds
    }

    $('#scale-factor').on('change', function() {
        const clickPositionX = localStorage.getItem('clickPositionX');
        const clickPositionY = localStorage.getItem('clickPositionY');
        const scaleFactor = parseFloat($(this).val());

        if (clickPositionX !== null && clickPositionY !== null) {
            updateAllHighResImages(clickPositionX, clickPositionY, scaleFactor);
        }
    });

    $('#init-adapter').on('click', function() {
        $.ajax({
            url: '/adapter/init',
            method: 'POST',
            success: function(response) {
                $('#adapter-message').text(response.message).removeClass('alert-danger').addClass('alert-success');
            },
            error: function(xhr) {
                $('#adapter-message').text(xhr.responseJSON.message).removeClass('alert-success').addClass('alert-danger');
            }
        });
    });

    $('#close-adapter').on('click', function() {
        $.ajax({
            url: '/adapter/close',
            method: 'POST',
            success: function(response) {
                $('#adapter-message').text(response.message).removeClass('alert-danger').addClass('alert-success');
            },
            error: function(xhr) {
                $('#adapter-message').text(xhr.responseJSON.message).removeClass('alert-success').addClass('alert-danger');
            }
        });
    });

    loadImages(); // Initial load of images
    pollForNewImages(); // Start polling for new images
});
