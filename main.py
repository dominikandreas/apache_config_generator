#!/usr/bin/python3
import os
from jinja2 import Template
import yaml
from subprocess import getoutput

apache_config_dir = "/etc/apache2/sites-enabled/"
config_path = "./config.yaml"

default_config = dict(
    defaults=dict(
        local_http_port=80,
        local_https_port=443,
        host="<hostname>",
        https_redirect=True,
        run_certbot=True
    )
)

forward_cmd = """ 
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule /(.*)           ws://{{ ip }}:{{ port }}/$1 [P,L]
  RewriteCond %{HTTP:Upgrade} !=websocket [NC]
  RewriteRule /(.*)           http://{{ ip }}:{{ port }}/$1 [P,L]
"""


template = Template("""\
<Virtualhost *:{{ local_http_port }}>
    ServerName {{ subdomain }}.{{ host }}

    RewriteEngine On
{%- if https_redirect %}
    RewriteCond %{SERVER_NAME} ={{ subdomain }}.{{ host }}
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
{%- else -%}
    """ + forward_cmd + """ 
{%- endif %}    

</Virtualhost>

{%- if https_redirect %}
<Virtualhost *:{{ local_https_port }}>
    ServerName {{ subdomain }}.{{ host }} 
    RewriteEngine On
    """ + forward_cmd + """ 
SSLCertificateFile /etc/letsencrypt/live/{{ subdomain }}.{{ host }}/fullchain.pem
SSLCertificateKeyFile /etc/letsencrypt/live/{{ subdomain }}.{{ host }}/privkey.pem
Include /etc/letsencrypt/options-ssl-apache.conf
</Virtualhost>
{%- endif %}    

""")


def check_apache_modules():
    required_mods = """proxy_module
    proxy_html_module
    proxy_http_module
    proxy_wstunnel_module
    rewrite_module
    ssl_module
    proxy_ajp_module"""
    installed_mods = getoutput("apache2ctl -M")
    for mod in required_mods.split():
        if mod not in installed_mods:
            print("WARNING: mod %s doesn't seem to be activated" % mod)


def render_template(name, variables):
    for entry in "local_http_port ip port host".split():
        assert entry in variables
    return template.render(subdomain=name, **variables)


def render_templates(config):
    defaults = config.pop("defaults")
    for name, props in config.items():
        props["host"] = props.get("host", defaults["host"])
    for name, variables in config.items():
        if name == "defaults":
            continue

        vars_local = defaults.copy()
        vars_local.update(variables)

        result = render_template(name, vars_local)
        path = os.path.abspath(apache_config_dir+"/"+name+".conf")
        if os.path.isfile(path):
            print("Not replacing existing config %s. Delete it to update" % path.lower().strip())
            continue
        print("Writing config %s" % path.lower().strip())
        with open(path, "w") as f:
            f.write(result)
    print(f"""you should execute \n

for domain in {" ".join([f"{name}.{props['host']}" for name, props in config.items()])}
do 
  certbot certonly --standalone -d $domain
done
""")

if __name__ == "__main__":
    if not os.path.isdir(os.path.dirname(config_path)):
        os.makedirs(os.path.dirname(config_path))
    if not os.path.isfile(config_path):
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        print("generated default config at %s" % config_path)
    else:
        check_apache_modules()
        with open(config_path, "r") as f:
            config = yaml.load(f)
            render_templates(config)
