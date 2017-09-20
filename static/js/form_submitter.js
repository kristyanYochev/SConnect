$(document).ready(function() {
    $('form').on('submit', function(e) {
        e.preventDefault()
        $.ajax({
            url: $(this).attr('action'),
            data: $(this).serialize(),
            type: "POST",
            success: function(data) {
                console.log(data)
                if (data.code == '1') {
                    window.location.href = data.url
                } else {
                    var snackbar = document.querySelector('#error-message')
                    snackbar.MaterialSnackbar.showSnackbar({message: data.error})
                }
            },
        })
    })
})
