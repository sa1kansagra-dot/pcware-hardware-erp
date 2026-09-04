import sys
import os
import io

# Ensure current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server import ERPRequestHandler

class WSGIRequestHandler(ERPRequestHandler):
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.status_code = 200
        self.status_phrase = "OK"
        self.response_headers = []
        self.headers_sent = False
        
        self.command = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "/")
        query = environ.get("QUERY_STRING", "")
        self.path = path + ("?" + query if query else "")
        self.request_version = "HTTP/1.1"
        self.close_connection = True
        
        # Setup rfile
        input_body = environ.get("wsgi.input")
        if input_body:
            try:
                content_length = int(environ.get("CONTENT_LENGTH") or 0)
            except (ValueError, TypeError):
                content_length = 0
            if content_length > 0:
                self.rfile = io.BytesIO(input_body.read(content_length))
            else:
                self.rfile = io.BytesIO()
        else:
            self.rfile = io.BytesIO()
            
        self.wfile = io.BytesIO()
        
        # Setup HTTPMessage headers
        from http.client import HTTPMessage
        self.headers = HTTPMessage()
        for k, v in environ.items():
            if k.startswith("HTTP_"):
                header_name = k[5:].replace("_", "-").title()
                self.headers[header_name] = v
            elif k in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                header_name = k.replace("_", "-").title()
                self.headers[header_name] = v

    def send_response(self, code, message=None):
        self.status_code = code
        self.status_phrase = message or ("OK" if code == 200 else str(code))

    def send_header(self, keyword, value):
        self.response_headers.append((keyword, str(value)))

    def end_headers(self):
        self.headers_sent = True

    def handle_request(self):
        method_name = f"do_{self.command}"
        if hasattr(self, method_name):
            getattr(self, method_name)()
        else:
            self.send_error(501, f"Unsupported method: {self.command}")

def application(environ, start_response):
    handler = WSGIRequestHandler(environ, start_response)
    handler.handle_request()
    
    status_str = f"{handler.status_code} {handler.status_phrase}"
    start_response(status_str, handler.response_headers)
    return [handler.wfile.getvalue()]

if __name__ == "__main__":
    from server import run_server
    run_server()
