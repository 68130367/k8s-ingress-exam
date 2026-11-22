import glob
import html
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SEED_NAME = os.environ.get("STUDENT_NAME", "[ชื่อ]")
SEED_SID = os.environ.get("STUDENT_ID", "[รหัสนักศึกษา]")
DATA_FILE = os.environ.get("DATA_FILE", "/data/portal.json")
PHOTO_GLOB = os.environ.get("PHOTO_GLOB", "/photo/photo.*")
PORT = int(os.environ.get("PORT", "8080"))
MAX_BODY = 4 * 1024

PAGE = """<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portal</title>
<style>
 body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
      font-family:system-ui,-apple-system,"Sarabun",sans-serif;background:#f4f6fb;color:#14213d}}
 .card{{background:#fff;padding:2rem 3rem;border-radius:1rem;text-align:center;
       box-shadow:0 4px 24px rgba(0,0,0,.1)}}
 img{{width:220px;height:220px;object-fit:cover;border-radius:50%;border:4px solid #14213d}}
 h1{{margin:1rem 0 .25rem}} p{{margin:.25rem 0;font-size:1.25rem}}
 small{{color:#777}}
</style></head><body><div class="card">
<img src="/photo" alt="photo">
<h1>{name}</h1>
<p>ID: {sid}</p>
<small>served by portal-367 &middot; pod {pod} &middot; node {node}</small>
</div></body></html>"""


def load():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return str(data["name"]), str(data["id"])
    except (OSError, ValueError, KeyError):
        return SEED_NAME, SEED_SID


def save(name, sid):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"name": name, "id": sid}, f, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


def find_photo():
    files = sorted(glob.glob(PHOTO_GLOB))
    return files[0] if files else None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _path(self):
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def _from_outside(self):
        # ingress-nginx always adds X-Real-IP / X-Forwarded-For; calls from
        # another pod (admin-367) go straight to the Service and carry neither.
        return "X-Real-IP" in self.headers or "X-Forwarded-For" in self.headers

    def do_GET(self):
        path = self._path()
        if path == "/healthz":
            return self._send(200, "ok", "text/plain")
        if path == "/":
            name, sid = load()
            body = PAGE.format(
                name=html.escape(name),
                sid=html.escape(sid),
                pod=html.escape(os.environ.get("HOSTNAME", "?")),
                node=html.escape(os.environ.get("NODE_NAME", "?")),
            )
            return self._send(200, body, "text/html; charset=utf-8")
        if path == "/photo":
            photo = find_photo()
            if not photo:
                return self._send(404, "no photo", "text/plain")
            ctype = mimetypes.guess_type(photo)[0] or "application/octet-stream"
            with open(photo, "rb") as f:
                return self._send(200, f.read(), ctype)
        if path == "/internal/config":
            if self._from_outside():
                return self._send(403, "forbidden", "text/plain")
            name, sid = load()
            return self._send(
                200,
                json.dumps({"name": name, "id": sid}, ensure_ascii=False),
                "application/json; charset=utf-8",
            )
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self._path() != "/internal/config":
            return self._send(404, "not found", "text/plain")
        if self._from_outside():
            return self._send(403, "forbidden", "text/plain")
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY:
            return self._send(413, "too large", "text/plain")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            name, sid = str(data["name"]).strip(), str(data["id"]).strip()
        except (ValueError, KeyError):
            return self._send(400, "bad request", "text/plain")
        if not name or not sid or len(name) > 200 or len(sid) > 50:
            return self._send(400, "bad request", "text/plain")
        save(name, sid)
        self._send(200, "ok", "text/plain")


if __name__ == "__main__":
    print(f"portal-367 listening on :{PORT}, data={DATA_FILE}", flush=True)
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
