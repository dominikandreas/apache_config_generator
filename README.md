# Apache Config Generator
## generate apache proxy configs with different subdomains

This is just a small script that I wrote automate my apache configurations for various subdomains and services.

In a nutshell it reads a subdomain, target ip and port from a config file and generates an apache config which will automatically proxy to that service if given subdomain matches.

This allows apache to behave as a subdomain dependent service proxy. 

### Example
You have homeassistant running on raspberrypi:8123 and would like to access it using home.mydomain.com. You can use a service like cloudflare to point this subdomain to your server, but you only want to show homeassistant for this specific subdomain. 

For this case you'd setup your config as 

```yaml
defaults:
  host: mydomain.de
  https_redirect: true
  local_http_port: 80
  local_https_port: 443
  ip: 'localhost'
  run_certbot: true
home:
  ip: 'raspberrypi'
  port: 8123
```

and run main.py to generate /etc/apache2/sites-enabled/ha.conf:

```conf
<Virtualhost *:80>
    ServerName home.mydomain.de

    RewriteEngine On
    RewriteCond %{SERVER_NAME} =home.mydomain.de
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]

</Virtualhost>
<Virtualhost *:443>
    ServerName home.mydomain.de
    RewriteEngine On

  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteRule /(.*)           ws://raspberrypi:8123/$1 [P,L]
  RewriteCond %{HTTP:Upgrade} !=websocket [NC]
  RewriteRule /(.*)           http://raspberrypi:8123/$1 [P,L]
</Virtualhost>
```
Afterwards the script presents the option to auto-generate valid ssl certificates and adjust the configuration using certbot-auto.
For this to work, certbot-auto needs to be preinstalled from here: https://certbot.eff.org/
