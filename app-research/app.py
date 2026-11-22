import html
import os
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

PORT = int(os.environ.get("PORT", "8080"))
DATA_FILE = os.environ.get("DATA_FILE", "/data/research.md")
SEED_FILE = os.environ.get("SEED_FILE", "/seed/research.seed.md")
MAX_BODY = 200 * 1024

STYLE = """
 body{margin:0;font-family:system-ui,-apple-system,"Sarabun",sans-serif;background:#f4f6fb;color:#14213d}
 main{max-width:52rem;margin:2rem auto;background:#fff;padding:2rem 2.5rem;border-radius:1rem;
      box-shadow:0 4px 24px rgba(0,0,0,.1)}
 p{line-height:1.8;text-indent:2rem} small{color:#777}
 textarea{width:100%;min-height:22rem;box-sizing:border-box;font:inherit;line-height:1.6;padding:.75rem}
 button{margin-top:.75rem;padding:.6rem 1.5rem;font-size:1rem;cursor:pointer}
 .ok{background:#e6f6ea;border:1px solid #2e9e4d;padding:.5rem 1rem;border-radius:.5rem}
"""


def head(title):
    return (
        f'<!doctype html><html lang="th"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title><style>{STYLE}</style></head><body><main>"
    )


def load():
    with open(DATA_FILE, encoding="utf-8") as f:
        return f.read()


def stats(text):
    return f"{len(text.split())} tokens (นับตามช่องว่าง) · {len(text)} ตัวอักษร"


def pod():
    return html.escape(os.environ.get("HOSTNAME", "?"))


def view_page():
    text = load()
    paras = "".join(f"<p>{html.escape(p)}</p>" for p in text.split("\n\n") if p.strip())
    return (
        head("Research")
        + "<h1>สรุปงานวิจัย</h1>"
        + paras
        + f"<small>{stats(text)} · served by app-research · pod {pod()}</small>"
        + "</main></body></html>"
    )


def edit_page(saved=False):
    text = load()
    banner = '<p class="ok">บันทึกเรียบร้อยแล้ว</p>' if saved else ""
    return (
        head("Edit research")
        + "<h1>แก้ไขสรุปงานวิจัย</h1>"
        + banner
        + f'<form method="post"><textarea name="content">{html.escape(text)}</textarea><br>'
        + '<button type="submit">บันทึก</button></form>'
        + f"<small>{stats(text)} · served by app-research · pod {pod()}</small>"
        + "</main></body></html>"
    )


def ensure_data():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        shutil.copyfile(SEED_FILE, DATA_FILE)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _path(self):
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def do_GET(self):
        p = self._path()
        if p == "/healthz":
            return self._send(200, "ok", "text/plain")
        if p == "/research":
            return self._send(200, view_page())
        if p == "/edit":
            return self._send(200, edit_page())
        if p == "/internal/content":
            # raw text for admin-367; ingress-nginx adds X-Real-IP, in-cluster calls do not
            if "X-Real-IP" in self.headers or "X-Forwarded-For" in self.headers:
                return self._send(403, "forbidden", "text/plain")
            return self._send(200, load(), "text/plain; charset=utf-8")
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self._path() != "/edit":
            return self._send(404, "not found", "text/plain")
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY:
            return self._send(413, "too large", "text/plain")
        form = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        content = form.get("content", [""])[0].replace("\r\n", "\n")
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, DATA_FILE)
        self._send(200, edit_page(saved=True))


if __name__ == "__main__":
    ensure_data()
    print(f"app-research listening on :{PORT}, data={DATA_FILE}", flush=True)
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
