import html
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

PORT = int(os.environ.get("PORT", "8080"))

PAGE = """<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>API</title>
<style>
 html,body{margin:0;height:100%}
 body{min-height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden;
      font-family:system-ui,-apple-system,"Sarabun",sans-serif;background:#14213d;color:#fff;
      transition:background 1s ease}
 .msg{font-size:clamp(3rem,12vw,10rem);font-weight:800;text-align:center;
      padding:1rem;line-height:1.25;perspective:700px}
 .msg span{display:inline-block;white-space:pre;will-change:transform,opacity,filter}
 small{position:fixed;bottom:.5rem;right:1rem;opacity:.5}

 body.s0{background:#0d1b2a}
 body.s0 .msg{animation:hue 4s linear infinite}
 body.s0 .msg span{color:hsl(calc(var(--i)*32) 95% 62%);animation:rise 1.4s ease-in-out infinite alternate;
      animation-delay:calc(var(--i)*70ms)}

 body.s1{background:#064e3b}
 body.s1 .msg span{animation:bounce 1s cubic-bezier(.3,.9,.4,1) infinite;animation-delay:calc(var(--i)*90ms)}

 body.s2{background:#12002b}
 body.s2 .msg span{color:#fff;text-shadow:0 0 6px #fff,0 0 16px #ff2bd6,0 0 34px #ff2bd6,0 0 70px #7c3aed;
      animation:neon 1.6s ease-in-out infinite;animation-delay:calc(var(--i)*120ms)}

 body.s3{background:#0a0a0a}
 body.s3 .msg span{text-shadow:-4px 0 #ff2a6d,4px 0 #05d9e8;animation:glitch 1.1s steps(1,end) infinite;
      animation-delay:calc(var(--i)*60ms)}

 body.s4{background:#1e1b4b}
 body.s4 .msg span{color:#fde68a;animation:flip 2.4s ease-in-out infinite;animation-delay:calc(var(--i)*110ms)}

 body.s5{background:#450a0a}
 body.s5 .msg span{color:#fecaca;opacity:0;animation:reveal 3.4s ease-out infinite;
      animation-delay:calc(var(--i)*140ms)}

 body.s6{background:#1a0500}
 body.s6 .msg span{color:#fff3b0;
      text-shadow:0 0 4px #fff,0 -4px 10px #ffdd00,0 -9px 16px #ff8800,0 -16px 26px #ff3300;
      animation:flame .9s ease-in-out infinite alternate;animation-delay:calc(var(--i)*-130ms)}

 @keyframes hue{to{filter:hue-rotate(360deg)}}
 @keyframes rise{from{transform:translateY(0) rotate(-3deg)}to{transform:translateY(-.12em) rotate(3deg)}}
 @keyframes bounce{0%,60%,100%{transform:translateY(0) scale(1,1)}
      15%{transform:translateY(-.45em) scale(.92,1.1)}30%{transform:translateY(0) scale(1.15,.85)}}
 @keyframes neon{0%,100%{opacity:1}45%{opacity:.95}50%{opacity:.35}55%{opacity:1}
      70%{text-shadow:0 0 4px #fff,0 0 10px #22d3ee,0 0 24px #22d3ee,0 0 50px #0ea5e9}}
 @keyframes glitch{0%,100%{transform:translate(0)}
      10%{transform:translate(-.04em,.02em) skewX(-8deg)}20%{transform:translate(.05em,-.02em)}
      30%{transform:translate(0)}60%{transform:translate(.03em,.03em) skewX(6deg);text-shadow:4px 0 #ff2a6d,-4px 0 #05d9e8}
      70%{transform:translate(0)}}
 @keyframes flip{0%,55%{transform:rotateY(0)}80%,100%{transform:rotateY(360deg)}}
 @keyframes reveal{0%{opacity:0;transform:scale(3.2);filter:blur(24px)}
      25%,85%{opacity:1;transform:scale(1);filter:blur(0)}100%{opacity:0;transform:scale(.6);filter:blur(12px)}}
 @keyframes flame{from{transform:translateY(0) scale(1,1);filter:brightness(1)}
      to{transform:translateY(-.06em) scale(1.04,1.1);filter:brightness(1.25)}}

 @media (prefers-reduced-motion:reduce){.msg,.msg span{animation:none!important}.msg span{opacity:1!important}}
</style></head><body>
<div class="msg">__TEXT__</div>
<small>served by api-367 &middot; pod __POD__ &middot; node __NODE__</small>
<script>
(function () {
  var el = document.querySelector(".msg");
  var raw = el.textContent;
  var parts = (window.Intl && Intl.Segmenter)
    ? Array.from(new Intl.Segmenter("th", {granularity: "grapheme"}).segment(raw), function (x) { return x.segment; })
    : Array.from(raw);
  el.setAttribute("aria-label", raw);
  el.textContent = "";
  parts.forEach(function (ch, i) {
    var s = document.createElement("span");
    s.textContent = ch;
    s.style.setProperty("--i", i);
    s.setAttribute("aria-hidden", "true");
    el.appendChild(s);
  });
  var styles = 7, k = 0;
  function next() {
    document.body.className = "s" + k;
    k = (k + 1) % styles;
  }
  next();
  setInterval(next, 4000);
})();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        raw = self.path.split("?", 1)[0]
        if raw == "/healthz":
            return self._send(200, b"ok", "text/plain")
        if raw == "/api-367" or raw.startswith("/api-367/"):
            text = (
                unquote(raw[len("/api-367/") :]) if raw.startswith("/api-367/") else ""
            )
            text = text or "(ใส่ข้อความต่อท้าย /api-367/)"
            body = (
                PAGE.replace("__POD__", html.escape(os.environ.get("HOSTNAME", "?")))
                .replace("__NODE__", html.escape(os.environ.get("NODE_NAME", "?")))
                .replace("__TEXT__", html.escape(text))
                .encode()
            )
            return self._send(200, body, "text/html; charset=utf-8")
        self._send(404, b"not found", "text/plain")


if __name__ == "__main__":
    print(f"api-367 listening on :{PORT}", flush=True)
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
