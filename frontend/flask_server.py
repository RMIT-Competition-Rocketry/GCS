#!/usr/bin/env python3

from flask import Flask, send_from_directory, abort
import os


# Initialise flask
APP = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')  # TODO: Load from config.ini?
VALID_FILE_EXTENSIONS = ('.html', '.css', '.js', '.png', '.jpg', '.ico')  # TODO: Determine other filetypes (fonts)


# Serve index page
@APP.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


# Serve static files
@APP.route('/<path:filename>')
def serve_html(filename):
    # Absolute filepath of request
    filepath = os.path.join(STATIC_DIR, filename)

    # Load files with valid extensions
    if filename.endswith(VALID_FILE_EXTENSIONS) and os.path.isfile(filepath):
        return send_from_directory(STATIC_DIR, filename)
    
    # Attempt to load filename as .html (so suffix isn't always required)
    elif os.path.isfile(filepath + ".html"):
        return send_from_directory(STATIC_DIR, filename + ".html")
    
    # 404 page not found
    else:
        abort(404)


if __name__ == "__main__":
    APP.run(debug=True)
