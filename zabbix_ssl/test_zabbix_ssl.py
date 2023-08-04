""" Zabbix SSL tests """
import zabbix_ssl

GOOGLE_HOST = 'google.com'
HTTPS_PORT = 443
GOOGLE_SSL_ISSUER = 'GTS CA 1C3'


def test_get_issuer():
    assert zabbix_ssl.get_issuer(GOOGLE_HOST, HTTPS_PORT) == GOOGLE_SSL_ISSUER


def test_get_validity():
    """ Test for get validity function
    Please let me know when Google's certificate will expire and the test will fail due to this reason.
    """
    assert zabbix_ssl.get_validity(GOOGLE_HOST, HTTPS_PORT) > 0


# TODO: Write test for Zabbix auto-discovery
def test_discover_ssl_servers():
    pass
