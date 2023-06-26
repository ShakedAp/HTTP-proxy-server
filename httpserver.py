"""
This module creates the custom HTTP Request Handler for a proxy server.

The ProxyHTTPHandler class inherits from the BaseHTTPRequestHandler class in the http.server module
and implements methods for handling the following HTTP methods: GET, POST, DELETE, OPTIONS, PUT, TRACE, CONNECT, HEAD.
It acts as an intermediary between the client and the destination server, forwarding incoming requests and processing the responses.

Author: Shaked Apter
Version: 1.0
"""

from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError 
from urllib.parse import urlparse

import shared_settings as ss


class ProxyHTTPHandler(BaseHTTPRequestHandler):
    """
        Custom HTTP Request Handler for a proxy server.
    
        This class inherits from the BaseHTTPRequestHandler class and implements methods for handling various HTTP methods.
        It acts as an intermediary between the client and the destination server, forwarding requests and processing responses.
    
        The class includes methods for handling GET, POST, DELETE, OPTIONS, PUT, TRACE, CONNECT, and HEAD requests.
        It also provides functionalities for filtering request URLs and IPs, handling exceptions, and logging server actions.
    """


    def log_message(self, format, *args):
        """
            Override of the original log message. 
            This function logs any action performed on the Proxy Server to the Log Queue. 
        """

        log_string = f"{self.log_date_time_string()} {self.address_string()} {format%args}"
        ss.sse_queue.put(log_string)


    def filter_request_url(self):
        """
            Filter the request URL based on the whitelist and blacklist.
            This method extracts the hostname from the request URL, and checks it against the URL whitelist and blacklist.
            The request is rejected if the URL is in the blacklist, or outside of the whitelist.

            Returns:
                bool: True if the request URL is allowed, False otherwise.
        """
        parsed_url = urlparse(self.path)
        url_hostname = parsed_url.hostname

        if ss.url_whitelist and url_hostname not in ss.url_whitelist:
            return False
        if url_hostname in ss.url_blacklist and url_hostname not in ss.url_whitelist:
            return False

        return True


    def filter_request_ip(self):
        """
            Filter the request IP based on the whitelist and blacklist.
            This method extracts the sender IP fro the request, and checks it against the IP whitelist and blacklist.
            The request is rejected if the IP is in the blacklist, or outside of the whitelist.

            Returns:
                bool: True if the sender IP is allowed, False otherwise.
        """

        client_ip, client_port = self.client_address

        if ss.ip_whitelist and client_ip not in ss.ip_whitelist:
            return False
        if client_ip in ss.ip_blacklist and client_ip not in ss.ip_whitelist:
            return False
        
        return True
        

    def handle_exception(self, e : Exception):
        """
            Handle different types of exceptions that may occur during request processing.

            The following exception types are handled:
            - `ValueError`: Sends a "Bad Request" response with a 400 status code.
            - `HTTPError`: Sends an error response with the code and reason provided by the exception.
            - `ConnectionResetError`: Logs a message indicating a connection reset by the remote host.
            - `TimeoutError`: Logs a message indicating a timeout while accessing the URL and sends a "Gateway Timeout" response with a 504 status code.
            - `URLError`: Sends a "Bad Gateway" response with a 502 status code and the reason from the exception.
            - `BrokenPipeError`: Logs a message indicating a client disconnection before the response could be sent.
            - `OSError`: Logs an OS error message and sends an "Internal Server Error" response with a 500 status code.
            - Other exceptions: Logs an unexpected error message and sends an "Internal Server Error" response with a 500 status code.

            Parameters:
                e (Exception): The exception object to handle.
        """

        if isinstance(e, ValueError):
            self.send_error(400, "Bad Request")
        elif isinstance(e, HTTPError):
            self.send_error(e.code, e.reason, str(e))
        elif isinstance(e, ConnectionResetError):
            ss.sse_queue.put("* connection reset by remote host *")
        elif isinstance(e, TimeoutError):
            ss.sse_queue.put("* timeout while accessing URL: {self.path} *")
            self.send_error(504, "Gateway Timeout")
        elif isinstance(e, URLError):
            self.send_error(502, e.reason   )
        elif isinstance(e, BrokenPipeError):
            ss.sse_queue.put("* client disconnected before response could be sent *")
        elif isinstance(e, OSError):
            ss.sse_queue.put(f"* OS Error: {e.strerror} *")
            self.send_error(500, "Internal Server Error")
        else:
            ss.sse_queue.put(f"* unexpected Error: {str(e)} *")
            self.send_error(500, "Internal Server Error")

    
    def filter_and_exceptions(func : callable):
        """
            Decorator function to filter requests and handle exceptions.

            This decorator wraps the given function `func` and adds filtering logic and exception handling to it.

            Parameters:
                func (callable): The function to be decorated.

            Returns:
                callable: The wrapped function with filtering and exception handling.
        """

        def wrapper(self, *args, **kwargs):
            try:
                # Check request IP and URL filters
                if not (self.filter_request_ip() and self.filter_request_url()):
                    self.send_error(403, "Access Denied")
                    return
                
                return func(self, *args, **kwargs)
            
            except Exception as e:
                self.handle_exception(e)

        return wrapper


    ##
    ## HTTP FUNCTIONS
    ##


    @filter_and_exceptions
    def do_GET(self):
        """
            Handle HTTP GET requests.

            This method handles HTTP GET requests received by the server. 
            If the resource is not in the cache or caching is not allowed, it fetches the resource from the specified URL,
            stores the response in the cache if caching is allowed, and sends the response back to the client.

            If the resource is present in the cache and caching is allowed, it sends the cached response directly to the client.
        """
        cached_response = ss.cache.get(self.path)

        if cached_response is None or not ss.allow_caching:
            # Fetch resource from the specified URL
            res = urlopen(self.path)
            res_content = res.read()

            cache_data = {'headers': res.headers.items(), 'content': res_content}
            if ss.allow_caching:
                ss.cache.set(self.path, cache_data, expire=ss.caching_timer)

            # Send response to the client
            self.send_response(res.status)
            for header, value in cache_data['headers']:
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(res_content)

        else:
            # Send cached response to the client
            ss.sse_queue.put(f"* sent data from cache {self.path} *")
            self.send_response(200, "OK (from cache)")
            cached_headers = cached_response['headers']
            cached_content = cached_response['content']

            for header, value in cached_headers:
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(cached_content)
    

    @filter_and_exceptions
    def do_POST(self):
        """
            Handle HTTP POST requests.

            This method handles HTTP POST requests received by the server. It reads the data, constructs a new
            request with the same data and headers, and sends it to the specified URL. It then sends the response
            received from the server back to the client.
        """
        # Read data from the request
        url = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Send the request to the server and get the response
        headers = {
            'Content-Type': self.headers['Content-Type'],
            'Content-Length': len(post_data)
        }   
        req = Request(url, post_data, headers=headers, method='POST')
        res = urlopen(req)
        res_content = res.read()

        # Send response to the client
        self.send_response(res.status)
        for header, value in res.headers.items():
            self.send_header(header, value)
        self.end_headers()
        
        self.wfile.write(res_content)
        

    @filter_and_exceptions
    def do_DELETE(self):
        """
            Handle HTTP DELETE requests.

            This method handles HTTP DELETE requests received by the server. It constructs a DELETE request with the same URL and headers
            as the received request and sends it to the specified URL. It then sends the response received from the server back to the client.
        """

        url = self.path

        # Get request headers
        headers = {}
        for header, value in self.headers.items():
            headers[header] = value

        # Create DELETE request
        req = Request(url, headers=headers, method='DELETE')
        res = urlopen(req)

        # Send response headers to the client
        self.send_response(res.status)
        for header, value in res.headers.items():
            self.send_header(header, value)
        self.end_headers()

        # Send response body to the client
        res_content = res.read()
        self.wfile.write(res_content)


    @filter_and_exceptions
    def do_OPTIONS(self):
        """
            Handle HTTP OPTIONS requests.

            This method handles HTTP OPTIONS requests received by the server. It sends a 200 OK response to the client, indicating that
            the requested HTTP methods are allowed. The response headers include the allowed methods and a content length of 0.
        """
        self.send_response(200)
        self.send_header('Allow', 'OPTIONS, GET, HEAD, POST, PUT, DELETE, CONNECT')
        self.send_header('Content-Length', '0')
        self.end_headers()


    @filter_and_exceptions
    def do_PUT(self):
        """
            Handle HTTP PUT requests.

            This method handles HTTP PUT requests received by the server. It reads the request body, constructs a PUT request with the
            received URL, headers, and body, and sends it to the specified URL. It then sends the response received from the server back to the client.
        """
        url = self.path

        # Get request headers
        headers = {}
        for header, value in self.headers.items():
            headers[header] = value

        # Read the request body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length)

        # Create PUT request
        req = Request(url, data=request_body, headers=headers, method='PUT')
        res = urlopen(req)

        # Send response headers to the client
        self.send_response(res.status)
        for header, value in res.headers.items():
            self.send_header(header, value)
        self.end_headers()

        # Send response body to the client
        res_content = res.read()
        self.wfile.write(res_content)


    @filter_and_exceptions
    def do_TRACE(self):
        """Handle HTTP TRACE requests."""
        self.send_error(405, "Method Not Allowed")

    @filter_and_exceptions
    def do_CONNECT(self):
        """Handle HTTP CONNECT requests."""
        self.send_error(405, "Method Not Allowed")

    @filter_and_exceptions
    def do_HEAD(self):
        """Handle HTTP HEAD requests."""
        # Forwards the response headers to the client
        res = urlopen(self.path)
        self.send_response(res.status)
        for header, value in res.headers.items():
            self.send_header(header, value)
        self.end_headers()