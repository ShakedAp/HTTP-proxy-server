# HTTP-proxy-server

This is a simple HTTP proxy server implemented in Python using the standard library, along with a management website built using Flask. The proxy server allows clients to send HTTP requests through the server, which then forwards those requests to the intended destination server and sends back the response. The management website provides a user interface to monitor and control the proxy server.


## Features

- HTTP Proxy Server: The proxy server accepts incoming HTTP requests and forwards them to the destination server.
- Caching: The server can cache responses from the destination server to improve performance for subsequent requests.
- IP & URL Blacklisting or Whitelisting: It is possible to blacklist or whitelist certain URLs or IPs to prevent clients from accessing specific resources, or prevent acess from specific clients.
- Management Website: The management website allows administrators to monitor the server, view logs, configure settings, and manage restricted resources.

## Installation & Usage

1. Clone the repository: ``` git clone https://github.com/ShakedAp/HTTP-proxy-server.git ```
2. Install the flask and diskcache libraries: ```pip install flask diskcache```
3. In `shared_settings.py` change the following variables:
    * `FLASK_HOST` to the web app ip (recommended to be local ip)
    * `FLASK_PORT` to the web app port
    * `PROXY_HOST` to the proxy server host ip
    * `PROXY_PORT` to the proxy server port
4. Run the app: ```python3 app.py``` 
5. Change the settings via the web app (port and host), and view the logs via the `/logpage` in the web app
6. Send HTTP packets to the proxy server host and port
