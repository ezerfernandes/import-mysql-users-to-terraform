provider "mysql" {
  endpoint = "{{ mysql_endpoint }}:{{ port }}"
  username = "{{ mysql_username }}"
  password = "{{ mysql_password }}"
}
