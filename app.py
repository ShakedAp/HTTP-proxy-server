"""
This module is the entry point for the program.
It runs a Flask server and starts a proxy server concurrently.

The Flask server handles HTTP requests and serves web applications using the main blueprint.
The proxy server acts as an intermediary for HTTP requests.

Author: Shaked Apter
Version: 1.0
"""

from flask import Flask

from main_blueprint import main_blueprint
import shared_settings as ss

from threading import Thread


def run_flask_app():
    """
        Run the Flask application.

        This function initializes a Flask application, registers a blueprint, changes it's logging level,
        and starts the Flask server to handle incoming requests.
    """

    flask_app = Flask(__name__)
    flask_app.register_blueprint(main_blueprint, url_prefix='/')
    
    # Change the Flask logging level
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    ss.sse_queue.put(f">> Flask Server Is Running on {ss.FLASK_HOST}:{ss.FLASK_PORT} <<")
    flask_app.run(host=ss.FLASK_HOST, port=ss.FLASK_PORT)

if __name__ == '__main__':
    proxy_thread = Thread(target=ss.run_proxy_server)
    proxy_thread.start()

    run_flask_app()
    ss.cache.close()