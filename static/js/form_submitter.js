function submit(e = null) {
    if (e) {e.preventDefault()}
    $.ajax({
        url: $('form').attr('action'), 
        data: $('form').serialize(),
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
}

$(document).ready(function() {
    $('form').on('submit', submit)
})