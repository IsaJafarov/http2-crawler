import socket
import ssl
import urllib.request  # the lib that handles the url stuff
from urllib.parse import urlparse

import network

'''
Load a list of domains from a remote file
'''
def get_domain_list():
    data = urllib.request.urlopen(
        'https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/domains.txt')

    domains = []
    for line in data:  # files are iterable
        domain = line.decode("utf-8")
        domain = domain[:-1]
        domains.append(domain)

    return domains


'''
Check if the web server uses HTTP/2
'''
def check_http2(domain_name):
    socket.setdefaulttimeout(5)

    try:
        host = urlparse(domain_name).netloc
        port = 443

        ctx = ssl.create_default_context()
        ctx.set_alpn_protocols(['h2', 'spdy/3', 'http/1.1'])

        conn = ctx.wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=host)
        conn.connect((host, port))

        pp = conn.selected_alpn_protocol()

        return pp == "h2"

    except Exception as e:
        print(e)

'''
Filter out domains that do not support HTTP/2
'''
def get_http2_domains(domains):
    http2_domains = []

    for domain in domains:

        try:
            print(domain)
            print(check_http2('https://' + domain))

            if check_http2('https://' + domain):
                http2_domains.append(domain)

        except Exception as e:
            continue

    return http2_domains

'''
Store data in a file
'''
def write_to_file(list, file_name):
    f = open(file_name, "w")
    for item in list:
        f.write(str(item)+'\n')
    f.close()

'''
Read data from a file
'''
def read_from_file(file_name):
    list = []
    with open(file_name, "r") as file:

        while True:
            line = file.readline()
            if not line:
                break
            item = line[:-1]
            list.append(item)

    return list


all_domains = get_domain_list()

http2_domains = get_http2_domains(all_domains[:10])

write_to_file(http2_domains, "http2_domains-test.txt")

# Since getting HTTP/2 domains takes so much time,
# next time read the data from the file instead of doing the process again
# http2_domains = read_from_file("http2_domains.txt")

domains_with_servers = network.get_servers_of_websites(http2_domains)

write_to_file(domains_with_servers, "domains_with_servers.txt")

