""" Simple parser for Apache configs """
import re


class ApacheParser:
    """ Simple parser for Apache configs """
    virt_block_start = r'\s*<VirtualHost (.*)?:(\d+)\s*>'
    virt_block_stop = r'\s*</VirtualHost>'
    virt_server_name = r'\s*ServerName\s(.*)$'
    virt_server_cert = r'\s*SSLCertificateFile\s(.*)$'

    def __init__(self, source):
        self.source = source

    def parse(self):
        server = []
        result = []
        for line in self.source.splitlines():
            match = re.match(self.virt_block_start, line)
            if match:
                server.append(['listen', match.group(2)])
            match = re.match(self.virt_server_name, line)
            if match:
                server.append(['server_name', match.group(1)])
            match = re.match(self.virt_server_cert, line)
            if match:
                server.append(['ssl_certificate', match.group(1)])
            if re.match(self.virt_block_stop, line):
                result.append([['server'], server])
                server = []
        return result

    def as_list(self):
        """
        Returns the list of tree.
        """
        return self.parse()


# Shortcut functions to respect Python's serialization interface
# (like pyyaml, picker or json)

def loads(source):
    return ApacheParser(source).as_list()
