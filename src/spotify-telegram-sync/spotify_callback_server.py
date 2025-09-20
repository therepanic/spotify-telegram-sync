from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from urllib.parse import urlencode, urlparse, parse_qs

client_id = os.getenv("SPOTIFY_CLIENT_ID")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
scope = os.getenv("SPOTIFY_SCOPE")

class SpotifyCallbackHandler(BaseHTTPRequestHandler):
    code_storage = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/auth":
            base_auth_url = "https://accounts.spotify.com/authorize"

            params = {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": scope
            }

            auth_url = f"{base_auth_url}?{urlencode(params)}"

            self.send_response(302)
            self.send_header("Location", auth_url)
            self.end_headers()
        elif parsed.path == "/callback":
            params = parse_qs(parsed.query)

            SpotifyCallbackHandler.code_storage = params.get("code", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Authorization code received! You can close this page.".encode('utf-8'))

class SpotifyCallbackServer:
    def __init__(self, host="0.0.0.0", port=7000):
        self.server = HTTPServer((host, port), SpotifyCallbackHandler)

    def start(self):
        print("Starting Spotify callback server...")
        self.server.serve_forever()

    def get_code(self):
        return SpotifyCallbackHandler.code_storage
    
    def set_code(self, code):
        SpotifyCallbackHandler.code_storage = code


