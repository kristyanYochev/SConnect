$(document).ready(function() {
  var socket = io.connect('http://' + document.domain + ":" + location.port)

  socket.on('connect', function() {
    socket.send('User has connected')
  })

  socket.on('message', function(msg) {
    $('#messages').append('<li>' + msg + "</li>")
  })

  $("#send").on('click', function() {
    socket.send($('#myMessage').val())
    $('#myMessage').val('')
  })
})
