output "server_public_ip" {
  description = "IP público do servidor Streamify"
  value       = aws_instance.streamify_server.public_ip
}

output "service_urls" {
  description = "URLs dos microsserviços"
  value = {
    music    = "http://${aws_instance.streamify_server.public_ip}:5001/music"
    playlist = "http://${aws_instance.streamify_server.public_ip}:5002/playlists"
    playback = "http://${aws_instance.streamify_server.public_ip}:5003/playback/status"
  }
}
