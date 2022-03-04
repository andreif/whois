import os
import re
import socket
from wsgiref import simple_server

IANA = "whois.iana.org"
DOMAIN_RX = re.compile(r"^[a-z0-9-]+\.[a-z]+$", flags=re.IGNORECASE)


def whois(domain, server=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((server or IANA, 43))
        sock.send(domain.encode() + b"\r\n")

        response = b""
        while True:
            response += (data := sock.recv(4096))
            if not data:
                break
    finally:
        sock.close()
    response = response.decode()
    if not server and (server := get_whois(response)):
        try:
            response = whois(domain=domain, server=server) + "\n\n" + ("-" * 100) + "\n\n" + response
        except:
            pass
    return response


def get_whois(text):
    if m := re.findall(r"^whois:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE):
        return m[0]


def app(env, start_response):
    path = env["PATH_INFO"][1:]
    if path and DOMAIN_RX.match(path):
        response = whois(path)
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [str(response).encode()]
    start_response("200 OK", [])
    return []


simple_server.ServerHandler.server_software = ""
port = int(os.environ.get("PORT", 8000))
with simple_server.make_server(host="", port=port, app=app) as httpd:
    print(f"Serving on port {port}...")
    httpd.serve_forever()
