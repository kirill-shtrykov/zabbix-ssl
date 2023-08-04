# Zabbix SSL Certificates monitoring

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Zabbix SSL certificate monitoring script and template with auto-discovery for Nginx and Apache web-servers

## Dependencies
- OpenSSL
- click
- dnspython
- pynginxconfig
- pyopenssl

## Install
1. Copy `zabbix_ssl` directory somewhere like `/opt` or `/etc/zabbix/scripts`
2. Make sure `zabbix_ssl.py` has executable bit: `chmod a+x zabbix_ssl.py`
3. Install requirements `pip install -r requirements.txt`
4. Copy `userparametr_ssl.conf` to `/etc/zabbix/zabbix.conf.d/`
5. Make ure paths in `userparametr_ssl.conf` are correct
6. Import `zbx_templates_ssl.xml` to Zabbix server
