locals {
  fleet_id = split("/", var.fleet_arn)[1]
}

variable "fleet_arn" {
  type = string
}

variable "name_prefix" {
  type = string
}
