function submit() {
    $.post(
        $('form').attr('action'), 
        $('form').serialize(), 
        function(data) {
            console.log(data)
            if (data.code == '1') {
                window.location.href = data.url
            } else {
                var snackbar = document.querySelector('#error-message')
                snackbar.MaterialSnackbar.showSnackbar({message: data.error})
            }
        }
    )

    if (grecaptcha) {
        grecaptcha.reset()
    }
}
