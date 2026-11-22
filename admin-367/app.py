import html
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode

PORT = int(os.environ.get("PORT", "8080"))
PORTAL_URL = os.environ.get("PORTAL_URL", "http://portal-367").rstrip("/")
RESEARCH_URL = os.environ.get("RESEARCH_URL", "http://app-research").rstrip("/")
WWW_HOST = os.environ.get("WWW_HOST", "www.iam-367.com")
MAX_BODY = 200 * 1024
TIMEOUT = 5

STYLE = """
 body{margin:0;min-height:100vh;font-family:system-ui,-apple-system,"Sarabun",sans-serif;
      background:#f4f6fb;color:#14213d}
 main{max-width:52rem;margin:2rem auto;background:#fff;padding:2rem 2.5rem;border-radius:1rem;
      box-shadow:0 4px 24px rgba(0,0,0,.1)}
 .buttons{display:flex;gap:1rem;flex-wrap:wrap;margin:1.5rem 0}
 a.btn,button{display:inline-block;padding:1rem 2rem;font-size:1.2rem;border:0;border-radius:.6rem;
      background:#14213d;color:#fff;text-decoration:none;cursor:pointer}
 a.back{display:inline-block;margin-top:1rem;color:#14213d}
 label{display:block;margin:.75rem 0 .25rem;font-weight:600}
 input,textarea{width:100%;box-sizing:border-box;font:inherit;padding:.6rem}
 textarea{min-height:22rem;line-height:1.6}
 .ok{background:#e6f6ea;border:1px solid #2e9e4d;padding:.5rem 1rem;border-radius:.5rem}
 .err{background:#fdeaea;border:1px solid #c0392b;padding:.5rem 1rem;border-radius:.5rem}
 small{color:#777}
"""


def page(title, body):
    pod = html.escape(os.environ.get("HOSTNAME", "?"))
    node = html.escape(os.environ.get("NODE_NAME", "?"))
    return (
        f'<!doctype html><html lang="th"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{STYLE}</style></head><body><main>"
        f"{body}<p><small>served by admin-367 &middot; pod {pod} &middot; node {node}</small></p>"
        "</main></body></html>"
    )


def banner(kind, text):
    return f'<p class="{kind}">{html.escape(text)}</p>' if text else ""


def http(method, url, data=None, ctype=None):
    req = urllib.request.Request(url, data=data, method=method)
    if ctype:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8")


def home_page():
    return page(
        "Admin",
        "<h1>หน้าจัดการ</h1><p>เลือกข้อมูลที่ต้องการแก้ไข</p>"
        '<div class="buttons"><a class="btn" href="/portal">แก้ portal (ชื่อ / id)</a>'
        '<a class="btn" href="/research">แก้ research (สรุปงานวิจัย)</a></div>'
        f"<p><small>ดูผลที่ http://{html.escape(WWW_HOST)}/ และ /research</small></p>",
    )


def portal_page(msg="", err=""):
    try:
        cfg = json.loads(http("GET", PORTAL_URL + "/internal/config"))
    except (OSError, ValueError) as e:
        return page(
            "แก้ portal",
            f"<h1>แก้ portal</h1>{banner('err', f'อ่านข้อมูลจาก portal-367 ไม่ได้: {e}')}"
            '<a class="back" href="/">&larr; กลับ</a>',
        )
    return page(
        "แก้ portal",
        "<h1>แก้ portal</h1>"
        + banner("ok", msg)
        + banner("err", err)
        + '<form method="post" action="/portal">'
        f'<label for="name">ชื่อ</label><input id="name" name="name" value="{html.escape(cfg["name"])}" required>'
        f'<label for="id">รหัสนักศึกษา (id)</label><input id="id" name="id" value="{html.escape(cfg["id"])}" required>'
        '<p><button type="submit">บันทึก</button></p></form>'
        '<a class="back" href="/">&larr; กลับ</a>',
    )


def research_page(msg="", err="", text=None):
    if text is None:
        try:
            text = http("GET", RESEARCH_URL + "/internal/content")
        except OSError as e:
            return page(
                "แก้ research",
                f"<h1>แก้ research</h1>{banner('err', f'อ่านข้อมูลจาก app-research ไม่ได้: {e}')}"
                '<a class="back" href="/">&larr; กลับ</a>',
            )
    return page(
        "แก้ research",
        "<h1>แก้ research</h1>"
        + banner("ok", msg)
        + banner("err", err)
        + f'<form method="post" action="/research"><textarea name="content">{html.escape(text)}</textarea>'
        '<p><button type="submit">บันทึก</button></p></form>'
        '<a class="back" href="/">&larr; กลับ</a>',
    )


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

    def _form(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY:
            return None
        raw = self.rfile.read(length).decode("utf-8")
        return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

    def do_GET(self):
        p = self._path()
        if p == "/healthz":
            return self._send(200, "ok", "text/plain")
        if p == "/":
            return self._send(200, home_page())
        if p == "/portal":
            return self._send(200, portal_page())
        if p == "/research":
            return self._send(200, research_page())
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        p = self._path()
        form = self._form()
        if form is None:
            return self._send(413, "too large", "text/plain")
        if p == "/portal":
            name, sid = form.get("name", "").strip(), form.get("id", "").strip()
            if not name or not sid:
                return self._send(400, portal_page(err="ต้องกรอกทั้งชื่อและ id"))
            try:
                http(
                    "POST",
                    PORTAL_URL + "/internal/config",
                    json.dumps({"name": name, "id": sid}, ensure_ascii=False).encode(
                        "utf-8"
                    ),
                    "application/json",
                )
            except (OSError, urllib.error.HTTPError) as e:
                return self._send(502, portal_page(err=f"บันทึกไม่สำเร็จ: {e}"))
            return self._send(200, portal_page(msg="บันทึกเรียบร้อยแล้ว"))
        if p == "/research":
            content = form.get("content", "").replace("\r\n", "\n")
            try:
                http(
                    "POST",
                    RESEARCH_URL + "/edit",
                    urlencode({"content": content}).encode("utf-8"),
                    "application/x-www-form-urlencoded",
                )
            except (OSError, urllib.error.HTTPError) as e:
                return self._send(
                    502, research_page(err=f"บันทึกไม่สำเร็จ: {e}", text=content)
                )
            return self._send(200, research_page(msg="บันทึกเรียบร้อยแล้ว"))
        self._send(404, "not found", "text/plain")


if __name__ == "__main__":
    print(
        f"admin-367 listening on :{PORT} portal={PORTAL_URL} research={RESEARCH_URL}",
        flush=True,
    )
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
