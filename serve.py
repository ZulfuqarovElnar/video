#!/usr/bin/env python3
"""HTTP Range (206) dəstəkli sadə server — video seek üçün vacibdir."""
import os, re, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return None

        ctype = self.guess_type(path)
        fs = os.stat(path)
        size = fs.st_size
        rng = self.headers.get("Range")

        if rng is None:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return open(path, "rb")

        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        length = end - start + 1

        self.send_response(206)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        f = open(path, "rb")
        f.seek(start)
        self._remaining = length
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8747
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Serving on http://localhost:{port} (Range destekli)")
    HTTPServer(("", port), RangeHandler).serve_forever()
