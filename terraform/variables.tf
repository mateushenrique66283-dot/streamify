variable "region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "Nome do key pair EC2 para acesso SSH (null = sem SSH)"
  type        = string
  default     = null
}

variable "ssh_allowed_cidr" {
  description = "CIDR autorizado a acessar a porta 22 (ex: 203.0.113.10/32)"
  type        = string
  default     = "127.0.0.1/32"
}
