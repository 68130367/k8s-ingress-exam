import http.client
import os
import sys
import time
from datetime import datetime

DOMAIN = os.environ.get("DOMAIN", "iam-367.com")
TARGET = os.environ.get("INGRESS_HOST", "ingress-nginx-controller.ingress-nginx.svc.cluster.local")
PORT = int(os.environ.get("INGRESS_PORT", "80"))
SID = os.environ.get("STUDENT_ID", "")
WWW = "www." + DOMAIN
ADMIN = "admin." + DOMAIN


def fetch(host, path, want, tries=10):
    code, body = 0, ""
    for _ in range(tries):
        try:
            conn = http.client.HTTPConnection(TARGET, PORT, timeout=5)
            conn.request("GET", path, headers={"Host": host})
            resp = conn.getresponse()
            code, body = resp.status, resp.read().decode("utf-8", "replace")
            conn.close()
        except OSError as err:
            code, body = 0, str(err)
        not_ready = code in (0, 503) or (code == 404 and want != 404)
        if not not_ready:
            break
        time.sleep(1)
    return code, body


def wait_until_ready(seconds=90):
    end = time.time() + seconds
    for host, path in ((WWW, "/"), (WWW, "/research"), (WWW, "/api-367/ready"), (ADMIN, "/")):
        while time.time() < end:
            code, _ = fetch(host, path, 200, tries=1)
            if code == 200:
                break
            time.sleep(2)


results = {"pass": 0, "fail": 0}


def check(name, host, path, want, needle=""):
    code, body = fetch(host, path, want)
    if code == want and (not needle or needle in body):
        results["pass"] += 1
        print(f"PASS  {name}  ({host}{path} -> {code})")
    else:
        results["fail"] += 1
        extra = f" และมีคำว่า '{needle}'" if needle else ""
        print(f"FAIL  {name}  ({host}{path} -> {code}, ต้องการ {want}{extra})")


print(f"# check (in-cluster)  {datetime.now():%F %T}  target={TARGET}:{PORT}  domain={DOMAIN}")
wait_until_ready()
check("portal / แสดงรหัสนักศึกษา", WWW, "/", 200, SID)
check("portal มีรูป", WWW, "/photo", 200)
check("research แสดงหน้าสรุป", WWW, "/research", 200, "สรุปงานวิจัย")
check("api-367 แสดงข้อความ (ASCII)", WWW, "/api-367/hello-k8s", 200, "hello-k8s")
check("api-367 แสดงข้อความ (ไทย)", WWW, "/api-367/%E0%B8%AA%E0%B8%A7%E0%B8%B1%E0%B8%AA%E0%B8%94%E0%B8%B5", 200, "สวัสดี")
check("api-367 กัน HTML injection", WWW, "/api-367/%3Cb%3Ex%3C%2Fb%3E", 200, "&lt;b&gt;x&lt;/b&gt;")
check("admin / มีปุ่มแก้ portal/research", ADMIN, "/", 200, "/portal")
check("admin /portal ดึงข้อมูล portal", ADMIN, "/portal", 200, SID)
check("admin /research มีกล่องแก้ไข", ADMIN, "/research", 200, "<textarea")
check("www ไม่เปิด /internal/config จากภายนอก", WWW, "/internal/config", 403)
check("www ไม่เปิดหน้า /edit ให้คนทั่วไป", WWW, "/edit", 404)
check("host ที่ไม่รู้จักได้ 404", "other." + DOMAIN, "/", 404)
print(f"---- pass={results['pass']} fail={results['fail']}")
sys.exit(1 if results["fail"] else 0)
