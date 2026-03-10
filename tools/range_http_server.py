"""
Local static server with HTTP Range support (for <audio> seeking).

Usage:
  python tools/range_http_server.py [--port 8000]

Why:
  Python's built-in `python -m http.server` on some setups does not respond
  with 206 Partial Content for Range requests, causing browsers to fail seeking
  in large mp3/m4a files (click cue -> always plays from start).
"""

from __future__ import annotations

import argparse
import os
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            return super().send_head()

        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        fs = os.fstat(f.fileno())
        size = fs.st_size

        range_header = self.headers.get("Range")
        if range_header:
            m = _RANGE_RE.match(range_header.strip())
            if not m:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                f.close()
                return None

            start_s, end_s = m.groups()
            if start_s == "" and end_s == "":
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                f.close()
                return None

            if start_s == "":
                # suffix range: last N bytes
                suffix_len = int(end_s)
                start = max(0, size - suffix_len)
                end = size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s != "" else size - 1

            if start >= size or end < start:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                f.close()
                return None

            end = min(end, size - 1)
            length = end - start + 1

            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()

            f.seek(start)
            self.range = (start, end)
            return f

        # No Range: behave like normal SimpleHTTPRequestHandler (but include Accept-Ranges)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self.range = None
        return f

    def copyfile(self, source, outputfile):
        # If Range set, copy only that slice.
        if getattr(self, "range", None):
            start, end = self.range
            remaining = end - start + 1
            bufsize = 64 * 1024
            while remaining > 0:
                chunk = source.read(min(bufsize, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
            return
        return super().copyfile(source, outputfile)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    server = ThreadingHTTPServer(("0.0.0.0", args.port), RangeRequestHandler)
    print(f"Serving with Range support on http://localhost:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

