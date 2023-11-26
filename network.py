import socket
import h2.connection
import h2.events
import ssl
import signal
from functools import partial
import time

def handle(signum, frame):
    raise Exception('Something went wrong')

def establish_tcp_connection(hostname):
    """
    This function establishes a client-side TCP connection. How it works isn't
    very important to this example. For the purpose of this example we connect
    to localhost.
    """
    return socket.create_connection((hostname, 443))

def get_http2_ssl_context():
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.keylog_filename = './keys.log'
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ctx.set_alpn_protocols(["h2"])

    return ctx

def negotiate_tls(tcp_conn, context, hostname):
    tls_conn = context.wrap_socket(tcp_conn, server_hostname=hostname)
    tls_conn.settimeout(5)
    negotiated_protocol = tls_conn.selected_alpn_protocol()
    if negotiated_protocol != "h2":
        raise RuntimeError("Didn't negotiate HTTP/2!")

    return tls_conn

def get_webserver_of_website(tls_connection, http2_connection, hostname):

    # Initiate the connection
    http2_connection.initiate_connection()
    tls_connection.sendall(http2_connection.data_to_send())

    # Send GET request
    headers = [
        (':method', 'GET'),
        (':path', '/'),
        (':authority', hostname),
        (':scheme', 'https')
    ]
    http2_connection.send_headers(1, headers, end_stream=True)
    tls_connection.sendall(http2_connection.data_to_send())

    while True:
        data = tls_connection.recv(65536)
        # pass the received raw data to http2_connection to convert it HTTP/2 events
        events = http2_connection.receive_data(data)

        for event in events:
            # print(event)
            if isinstance(event, h2.events.ResponseReceived):
                # print('ResponseReceived')
                # print(event)
                # print(event.stream_id)
                response_headers = event.headers
                for header in response_headers:
                    if header[0] == b'server':
                        server = header[1].decode()
                        return server
                return None

def get_servers_of_websites(domains):

    # Set up your TLS context.
    context = get_http2_ssl_context()

    domains_with_servers = []

    for hostname in domains:

        # the program sometimes hangs in case of some specific hostnames.
        # if the process for a hostname takes loger than 20 seconds, skip it.
        signal.signal(signal.SIGALRM, handle)
        signal.alarm(20)

        webserver = None
        try:

            # Receive a TCP connection.
            connection = establish_tcp_connection(hostname)
            # Wrap the connection in TLS and validate that we negotiated HTTP/2
            tls_connection = negotiate_tls(connection, context, hostname)
            # Create a client-side H2 connection.
            http2_connection = h2.connection.H2Connection()
            webserver = get_webserver_of_website(tls_connection, http2_connection, hostname)
            print(hostname, ' - ', webserver)
        except Exception as e:
            print(hostname, ' - ', str(e))
        domains_with_servers.append((hostname, webserver))

    return domains_with_servers
