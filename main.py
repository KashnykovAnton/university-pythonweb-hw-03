import mimetypes
import json
from datetime import datetime
from pathlib import Path
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
DATA_FILE = STORAGE_DIR / "data.json"

jinja = Environment(loader=FileSystemLoader("templates"))


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case "/read":
                self.render_template("read.jinja")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)

    def do_POST(self):
        size = self.headers.get("Content-Length")
        body = self.rfile.read(int(size)).decode("utf-8")
        parse_body = urllib.parse.unquote_plus(body)
        r = {
            key: value for key, value in [el.split("=") for el in parse_body.split("&")]
        }
        print(r)

        self.save_message(r)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def save_message(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # message_data = {
        #     "username": data.get("username", ""),
        #     "message": data.get("message", ""),
        # }

        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        else:
            existing_data = {}

        existing_data[timestamp] = data

        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def render_template(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = {}

        template = jinja.get_template(filename)
        content = template.render(messages=data)
        self.wfile.write(content.encode())

    def send_static(self, filename, status=200):
        self.send_response(status)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

def run():
    server_address = ("", 3000)
    httpd = HTTPServer(server_address, MyHandler)
    print("Starting server on port 3000...")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        httpd.server_close()
        print("Server has been stopped")


if __name__ == "__main__":
    run()
