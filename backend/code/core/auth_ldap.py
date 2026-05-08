import ssl

from ldap3 import Connection, Server, Tls

from middlewares.i18n import _

from .config import Settings
from .exceptions import IncorrectCredentials, LdapConnectionError

settings = Settings()


# LDAP server auth
def ldap_connect(username, password):
    settings = Settings()
    # Set TLS configuration based on settings.ldap_verify_ssl
    if settings.ldap_verify_ssl:
        tls_configuration = Tls(validate=ssl.CERT_REQUIRED)
    else:
        tls_configuration = Tls(validate=ssl.CERT_NONE)
    # Create connection to LDAP server
    ldap_server = Server(
        settings.ldap_host,
        port=settings.ldap_port,
        use_ssl=True,
        connect_timeout=10,
        tls=tls_configuration,
    )
    try:
        # Connect to LDAP server with provided username and password
        ldap_connection = Connection(
            ldap_server,
            user=f"{settings.ldap_attr_user}={username},{settings.ldap_dn_people}",
            password=password,
            raise_exceptions=True,
        )
        ldap_connection.start_tls()
        if ldap_connection.bind():
            return ldap_connection
        else:
            raise IncorrectCredentials()
    except Exception as e:
        # TODO: add more granular error messages
        raise LdapConnectionError()
