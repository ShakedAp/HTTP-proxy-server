"""
This module creates the blueprint for the Flask Application.

In the web-app there are 3 main pages:
1. Home Page, a page to set the proxy server settings.
2. Log Page, a page to view all of the server logs.
3. Data Route, to handle the AJAX requests from the client, related to the logpage.

Author: Shaked Apter
Version: 1.0
"""


from flask import Blueprint, render_template, request, jsonify
from threading import Thread

import shared_settings as ss


main_blueprint = Blueprint('main_blueprint', __name__)

@main_blueprint.route('/', methods=["POST", "GET"])
def home_page():

    if request.method == "POST":
        if 'toggle_server' in request.form:
            if not ss.proxy_server_running:
                proxy_thread = Thread(target=ss.run_proxy_server)
                proxy_thread.start()
            else:
                ss.http_server.shutdown()

        if 'send_filters' in request.form:
            ss.url_blacklist = request.form['url_blacklist'].replace(' ', '').split(',')
            ss.url_whitelist = request.form['url_whitelist'].replace(' ', '').split(',')
            ss.ip_blacklist = request.form['ip_blacklist'].replace(' ', '').split(',')
            ss.ip_whitelist = request.form['ip_whitelist'].replace(' ', '').split(',')

            ss.url_blacklist = [x for x in ss.url_blacklist if x != '']
            ss.url_whitelist = [x for x in ss.url_whitelist if x != '']
            ss.ip_blacklist = [x for x in ss.ip_blacklist if x != '']
            ss.ip_whitelist = [x for x in ss.ip_whitelist if x != '']

            ss.sse_queue.put("> Client updated url filter lists, and ip filter lists <")

        
        if 'clear_cache' in request.form and ss.cache is not None:
            ss.cache.clear()
            ss.sse_queue.put("> Client cleared cache <")


        if 'send_caching' in request.form:
            if 'allow_cache' in request.form:
                ss.allow_caching = True
            else:
                ss.allow_caching = False

            ss.caching_timer = int(request.form['cache_time'])        

            ss.sse_queue.put(f"> Client updated caching to be {ss.allow_caching} <")
            ss.sse_queue.put(f"> Client updated caching timer to be {ss.caching_timer} seconds <")


    url_blacklist_text, url_whitelist_text = ', '.join(ss.url_blacklist), ', '.join(ss.url_whitelist)
    ip_blacklist_text, ip_whitelist_text = ', '.join(ss.ip_blacklist), ', '.join(ss.ip_whitelist)

    filter_input_data = {'url_blacklist': url_blacklist_text, 'url_whitelist': url_whitelist_text,
                   'ip_blacklist': ip_blacklist_text, 'ip_whitelist': ip_whitelist_text}

    button_color = '#eb4034'
    if ss.proxy_server_running:
        button_color = '#2ee649'

    return render_template("index.html",
                           btn_color = button_color,
                           caching_timer=ss.caching_timer, 
                           filter_input_data=filter_input_data)

@main_blueprint.route('/logpage')
def log_page():
    return render_template("logpage.html")


@main_blueprint.route('/data')
def data():
    send_data = list(ss.sse_queue.queue)
    ss.sse_queue.queue.clear()

    # print logging data to the shell as well as the web page
    # for d in send_data:
    #     print(d)

    return jsonify(send_data)
