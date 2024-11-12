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
                            const link = $('<a></a>').attr('href', '/media/' + image.image);
                            const img = $('<img>').attr('src', '/media/' + image.thumbnail).attr('alt', 'Thumbnail').addClass('img-fluid');
                            link.append(img);
                            thumbnail.append(link);
                            thumbnailColumn.append(thumbnail);

                            const highResImg = $('<img>').attr('src', '/media/' + image.image).attr('alt', 'High Resolution').addClass('img-fluid high-res');
                            highResColumn.append(highResImg);
                        }
                        let configInfo = 'Exposure: ' + image.meta.exposure + ', Gain: ' + image.meta.gain;
                        if (image.meta.focus !== null) {
                            configInfo += ', Focus: ' + image.meta.focus;
                        }
                        if (image.meta.aperture !== null) {
                            configInfo += ', Aperture: ' + image.meta.aperture;
                        }
                        configColumn.append('<div class="config">' + configInfo + '</div>');
                        row.append(thumbnailColumn, highResColumn, configColumn);
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
            const fullResImgSrc = thumbnail.parent().attr('href').replace('thumbnail_', ''); // Full-resolution image path

            // Log the full-resolution image path
            console.log('Full Resolution Image Path:', fullResImgSrc);

            // Create the high-resolution image element
            const highResImg = $('<img>')
		  .attr('src', fullResImgSrc)
		  .attr('alt', 'High Resolution')
		  .addClass('high-res');

            // Append the high-resolution image to the corresponding high-res container
            const highResContainer = thumbnail.closest('tr').find('.high-res-container');
            highResContainer.empty().append(highResImg);
            highResImg.show(); // Show the high-res image

            // Adjust position based on mouse movement
            thumbnail.on('mousemove', function(e) {
		const offset = thumbnail.offset();
		const x = e.pageX - offset.left;     // Get mouse x relative to the thumbnail
		const y = e.pageY - offset.top;      // Get mouse y relative to the thumbnail

		// Scale the position based on the high-res image and thumbnail size
		const scaleFactor = highResImg.width() / thumbnail.width();
		const newLeft = -(x * scaleFactor - (highResImg.width() / 2));
		const newTop = -(y * scaleFactor - (highResImg.height() / 2));

		// Move the high-res image based on calculated positions
		highResImg.css({
                    left: newLeft + 'px',
                    top: newTop + 'px',
                    position: 'absolute'
		});
            });

	}, function() {
            // Clear the high-res image when the mouse leaves
            $(this).closest('tr').find('.high-res-container').empty();
	});
    }
    

    loadImages(); // Initial load of images
});
