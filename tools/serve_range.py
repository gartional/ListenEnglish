"""
HTTP server with Range request (206) support so audio/video can seek.
Usage: python tools/serve_range.py [port]
Run from project root so that content/mock17/ etc. are served correctly.
"""
import os
import re
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler


def copy_byte_range(infile, outfile, start=None, stop=None, bufsize=16 * 1024):
    if start is not None:
        infile.seek(start)
    while True:
        if stop is not None:
            to_read = min(bufsize, stop + 1 - infile.tell())
            if to_read <= 0:
                break
        else:
            to_read = bufsize
        buf = infile.read(to_read)
        if not buf:
            break
        outfile.write(buf)
        if stop is not None and infile.tell() > stop:
            break


BYTE_RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)$")


def parse_byte_range(byte_range):
    if not byte_range or not byte_range.strip():
        return None, None
    m = BYTE_RANGE_RE.match(byte_range.strip())
    if not m:
        raise ValueError("Invalid byte range")
    first = int(m.group(1))
    last_str = m.group(2)
    last = int(last_str) if last_str else None
    if last is not None and last < first:
        raise ValueError("Invalid byte range")
    return first, last


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        if "Range" not in self.headers:
            self.range = None
            return super().send_head()
        try:
            self.range = parse_byte_range(self.headers["Range"])
        except ValueError:
            self.send_error(400, "Invalid byte range")
            return None
        first, last = self.range

        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_len = fs.st_size
        if first >= file_len:
            f.close()
            self.send_error(416, "Requested Range Not Satisfiable")
            return None

        if last is None or last >= file_len:
            last = file_len - 1
        response_length = last - first + 1

        self.send_response(206)
        self.send_header("Content-type", self.guess_type(path))
        self.send_header("Content-Range", "bytes %s-%s/%s" % (first, last, file_len))
        self.send_header("Content-Length", str(response_length))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        return super().end_headers()

    def copyfile(self, source, outputfile):
        if not getattr(self, "range", None):
            return super().copyfile(source, outputfile)
        start, stop = self.range
        copy_byte_range(source, outputfile, start, stop)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(("127.0.0.1", port), RangeRequestHandler)
    print("Serving with Range support at http://127.0.0.1:%s" % port)
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
