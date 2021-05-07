# Apache Config Generator
## generate apache proxy configs with different subdomains

This is just a small script that I wrote automate my apache configurations for various subdomains and services.

In a nutshell it reads a subdomain, target ip and port from a config file and generates an apache config which will automatically proxy to that service if given subdomain matches.

This allows apache to behave as a subdomain dependent service proxy. 

### Example
You have homeassistant running on localhost:8123 and would like to access it using home.mydomain.com. You can use a service like cloudflare to point this subdomain to your server, but you only want to show homeassistant for this specific subdomain. 

For this case you'd setup your config as 

```yaml
defaults:
  host: mydomain.de
  local_http_port: 80
homeassistant:
  ip: localhost
  port: 8123

```

and run main.py to generate /etc/apache2/sites-enabled/homeassistant.conf

```conf
<Virtualhost *:80>
    ServerName homeassistant.mydomain.de
    ProxyPass / http://localhost:8123/
    ProxyPassReverse / http://localhost:8123/

    <Location "/ws">
       ProxyPass "ws://localhost:8123/ws"
    </Location>
</Virtualhost>
```

