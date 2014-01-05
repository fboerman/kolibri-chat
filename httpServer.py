__author__ = 'williewonka'
__version__ = 1.0

from http.server import BaseHTTPRequestHandler, HTTPServer
from os.path import splitext, basename
import mimetypes

class httpRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        allowedtypes = [".html", ".css", ".js", ".json", ".svg", ".eot", ".ttf", ".woff"]
        origin = self.request.getpeername()[0]
        # rootdir = "D:/PycharmProjects/Kolibri_Chat/http"
        filetype =  splitext(basename(self.path))[1]
        rootdir = "http"
        if filetype not in allowedtypes and filetype != "":
            self.send_response(403)
            # print("Client from " + origin + " asked for forbidden file " + self.path)
            return

        filepath = ""
        if self.path == "/":
            filepath = rootdir + "/kolibri.html"
            filetype = ".html"
        else:
            filepath = rootdir + self.path

        try:
            stream = open(filepath, 'rb')
        except IOError:
            # print("GET request to nonexisting file " + self.path + " from client " + origin)
            self.send_response(404)
            return

        self.send_response(200)
        try:
            mime = mimetypes.types_map[filetype]
        except:
            mime = 'application/octet-stream'
        self.send_header('content-type', mime)
        self.end_headers()
        self.wfile.write(stream.read())
        stream.close()
        # print("GET request to file " + self.path + " answered to client " + origin)
        return


    def do_POST(self):
        self.send_response(403)
        return

print("http server is starting ...")
mimetypes.init()
server_address = ("192.168.0.104", 80)
server = HTTPServer(server_address, httpRequestHandler)
print("http server is running at " + server_address[0] + ":" + str(server_address[1]))
server.serve_forever()