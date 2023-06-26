"""
This module provides the shared settings for the HTTP proxy server.

Author: Shaked Apter
Version: 1.0
"""

from httpserver import ProxyHTTPHandler
from http.server import ThreadingHTTPServer

import queue
import diskcache

FLASK_HOST, FLASK_PORT = '127.0.0.1', 8000 # Settings web app HOST and PORT 
PROXY_HOST, PROXY_PORT = '192.168.68.118', 8800 # Proxy server HOST and PORT

CACHE_PATH = '/tmp/mycache' # Path to the cache folder

sse_queue = queue.Queue()
cache = diskcache.Cache(CACHE_PATH)

http_server = ThreadingHTTPServer((PROXY_HOST, PROXY_PORT), ProxyHTTPHandler)

url_whitelist = []
url_blacklist = []

ip_whitelist = []
ip_blacklist = []

proxy_server_running = False
allow_caching = True
caching_timer = 60

def run_proxy_server():
    """
        Runs the proxy server on the specified host and port.
        This function starts the proxy server, listens for incoming requests, and serves them indefinitely.
        It updates a global variable, `proxy_server_running`, to indicate the server's status.
    """
    global proxy_server_running

    sse_queue.put(f">> Proxy Server Is Running on {PROXY_HOST}:{PROXY_PORT} <<")
    proxy_server_running = True
    http_server.serve_forever()
    proxy_server_running = False
    sse_queue.put(f">> The Proxy Server has stopped <<")
