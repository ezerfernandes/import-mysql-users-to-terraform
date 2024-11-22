{% for u in user_grants_list %}
resource "mysql_user" "{{ user.terraform_id }}" {
  user = "{{ user.user }}"
  host = "{{ user.host }}"
}

{% for grant in user.grants %}
resource "mysql_grant" "{{ user.terraform_id }}_grants{{ loop.index }}" {
  user       = mysql_user.{{ user.terraform_id }}.user
  host       = mysql_user.{{ user.terraform_id }}.host
  database   = "{{ grant.database }}"
  table      = "{{ grant.table }}"
  privileges = {{ grant.privileges }}
{% if grant.grant %}  grant      = {{ grant.grant }}{% endif %}
{% if grant.tls_option %}  tls_option = {{ grant.tls_option }}{% endif %}
}

{% endfor %}
{% endfor %}