""" Zabbix SSL
Zabbix SSL certificate monitoring script and template with auto-discovery

Version: 0.0.6
URL: https://github.com/kirill-shtrykov/zabbix-ssl
Author: Kirill Shtrykov <kirill@shtrykov.com>
Website: https://shtrykov.com
"""
import dataclasses
import json
import os
import re
import socket
import ssl
from datetime import datetime
from typing import List

import click
import pynginxconfig

from .apacheconfig import loads

NGINX_CONFIG_DIR = '/etc/nginx/'
APACHE_CONFIG_DIR = '/etc/apache'
PUBLIC_DNS = '1.1.1.1'


@dataclasses.dataclass
class Server:
    name: str = ''
    port: int = 0
    cert: str = ''


def get_issuer(hostname: str, port: int) -> str:
    """ Gets an SSL certificate issuer using the OpenSSL library

    Arguments:
        hostname (str): host with SSL certificate
        port (str): port with SSL certificate

    Returns:
        str: certificate issuer common name
    """
    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(3.0)

    conn.connect((hostname, port))
    ssl_info = conn.getpeercert()
    issuer = {}
    # getpeercert return `issuer` as "tuple of tuples with tuples"
    for row in ssl_info['issuer']:
        issuer.update(dict((k, v) for k, v in row))
    return issuer['commonName']


def get_validity(hostname: str, port: int) -> int:
    """ Obtains the validity period of a certificate in days using the OpenSSL library

    Arguments:
        hostname (str): host with SSL certificate
        port (str): port with SSL certificate

    Returns:
        int: validity period of a certificate in days
    """
    ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'
    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(3.0)

    conn.connect((hostname, port))
    ssl_info = conn.getpeercert()
    end = datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)
    return (end - datetime.today()).days


def get_server(block: list) -> Server:
    """ Returns server object from configuration block

    Parameters:
        block (list): Configuration block, list of strings

    Returns:
        Server: server/host object from configuration block
    """
    server = Server()
    for line in block[1]:
        if isinstance(line, dict):
            continue
        if line[0] == 'listen':
            server.port = line[1].split()[0]
        if line[0] == 'server_name':
            names = line[1].split()
            if len(names) > 1:
                for name in names:
                    if name[0].isalpha():
                        server.name = name
                        break
            else:
                server.name = line[1]
        if line[0] == 'ssl_certificate':
            server.cert = line[1]
    return server


def get_nginx_servers() -> List[Server]:
    """ Parses Nginx configs for servers and return them

    Returns:
        List[Server]: list of configured Nginx servers
    """
    if not os.path.exists(NGINX_CONFIG_DIR):
        return []
    files = [f for f in os.listdir(NGINX_CONFIG_DIR)
             if os.path.isfile(os.path.join(NGINX_CONFIG_DIR, f))]
    servers = []
    for file in files:
        config = ''
        with open(os.path.join(NGINX_CONFIG_DIR, file), encoding='utf-8') as fh:
            level = 0
            found = False
            for line in fh:
                if re.match(re.compile(r'^\s*server\s*{'), line):
                    found = True
                if '{' in line:
                    level += 1
                if '}' in line:
                    level -= 1
                    if found and level == 0:
                        config += line
                        found = False

                if found and level == 0:
                    config += line
                    continue

                if found and level > 0:
                    config += line

        if config == '':
            continue

        parsed = pynginxconfig.NginxConfig()
        parsed.load(config)
        for block in parsed:
            if block['name'] == 'server':
                server = get_server(['', block['value']])
                if server.cert != '':
                    servers.append(server)
    return servers


def get_apache_servers() -> List[Server]:
    """ Parses Apache configs for virtual hosts and return them

    Returns:
        List[Server]: list of configured Apache virtual hosts
    """
    if not os.path.exists(APACHE_CONFIG_DIR):
        return []
    files = [f for f in os.listdir(APACHE_CONFIG_DIR)
             if os.path.isfile(os.path.join(APACHE_CONFIG_DIR, f))]
    servers = []
    for file in files:
        with open(os.path.join(APACHE_CONFIG_DIR, file), encoding='utf-8') as fh:
            config = fh.read()
            for block in loads(config):
                server = get_server(block)
                if server.cert != '':
                    servers.append(server)
    return servers


def discover_ssl_servers() -> str:
    """ Discovers SSL servers in Nginx and Apache configs and returns JSON in Zabbix auto-discovery format

    Returns:
        str: JSON in Zabbix auto-discovery format
    """
    data = []
    for server in [*get_nginx_servers(), *get_apache_servers()]:
        data.append({
            '{#DOMAIN}': server.name,
            '{#PORT}': server.port.split(':')[-1],
            '{#CERT}': server.cert}
        )
    return json.dumps({'data': data})


@click.command()
@click.argument('command', type=click.Choice(['discover', 'issuer', 'validity']))
@click.option('-h', '--host', type=str, help='host for checking')
@click.option('-p', '--port', type=click.IntRange(min=1, max=65535), help='port for checking')
def main(command: str, host: str, port: int):
    """ Zabbix SSL certificate monitoring script and template with auto-discovery """

    if command in ['issuer', 'validity'] and (not host or not port):
        raise click.UsageError('For "issuer" and "validity" commands "host" and "port" options are required')

    match command:
        case 'discover':
            print(discover_ssl_servers())
        case 'issuer':
            print(get_issuer(host, port))
        case 'validity':
            print(get_validity(host, port))


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter
