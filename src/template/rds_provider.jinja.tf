data "aws_db_instances" "{{ db_instance_terraform_id }}" {
  filter {
    name   = "db-instance-id"
    values = ["{{ db_instance_id }}"]
  }
}

provider "mysql" {
  endpoint = "${data.aws_db_instances.{{ db_instance_terraform_id }}.db_instance_endpoint}"
  username = "${data.aws_db_instances.{{ db_instance_terraform_id }}.db_instance_username}"
  password = "${data.aws_db_instances.{{ db_instance_terraform_id }}.db_instance_password}"
}