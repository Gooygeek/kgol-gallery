#! /usr/bin/env python
import sys
import os
import json

tags = sys.argv[1:]
print(tags)

#TODO: Convert the input into a logical expression
#TODO: Find all images that match the logical expression
#TODO: Generate the html page
#TODO: Start the server

import http.server
import socketserver

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
