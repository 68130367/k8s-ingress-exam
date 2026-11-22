#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."

: "${INGRESS_IP:?ตั้ง INGRESS_IP ก่อน เช่น INGRESS_IP=192.168.214.139}"
PORT="${INGRESS_PORT:-80}"
SID="$(grep -E '^STUDENT_ID=' config.env | cut -d= -f2-)"
DOMAIN="${DOMAIN:-iam-367.com}"
WWW="www.${DOMAIN}"; ADMIN="admin.${DOMAIN}"

pass=0; fail=0
req() { curl -s -m 10 --resolve "$1:${PORT}:${INGRESS_IP}" -w '\nSTATUS:%{http_code}' "http://$1:${PORT}$2"; }
t() {
  local name="$1" host="$2" path="$3" want="$4" needle="${5:-}" out code body i
  for i in $(seq 1 10); do
    out="$(req "$host" "$path")"; code="${out##*STATUS:}"; body="${out%STATUS:*}"
    if [[ "$code" == "503" || ( "$code" == "404" && "$want" != "404" ) ]]; then sleep 1; else break; fi
  done
  if [[ "$code" == "$want" ]] && { [[ -z "$needle" ]] || grep -qF -- "$needle" <<<"$body"; }; then
    echo "PASS  $name  ($host$path -> $code)"; pass=$((pass+1))
  else
    echo "FAIL  $name  ($host$path -> $code, ต้องการ $want${needle:+ และมีคำว่า '$needle'})"; fail=$((fail+1))
  fi
}

{
echo "# check.sh  $(date '+%F %T')  target=${INGRESS_IP}:${PORT}  domain=${DOMAIN}"
t "portal / แสดงรหัสนักศึกษา"        "$WWW"   /                      200 "$SID"
t "portal มีรูป"                     "$WWW"   /photo                 200
t "research แสดงหน้าสรุป"            "$WWW"   /research              200 "สรุปงานวิจัย"
t "api-367 แสดงข้อความ (ASCII)"      "$WWW"   /api-367/hello-k8s     200 "hello-k8s"
t "api-367 แสดงข้อความ (ไทย)"        "$WWW"   /api-367/%E0%B8%AA%E0%B8%A7%E0%B8%B1%E0%B8%AA%E0%B8%94%E0%B8%B5 200 "สวัสดี"
t "api-367 กัน HTML injection"       "$WWW"   '/api-367/%3Cb%3Ex%3C%2Fb%3E' 200 "&lt;b&gt;x&lt;/b&gt;"
t "admin / มีปุ่มแก้ portal/research" "$ADMIN" /                     200 "/portal"
t "admin /portal ดึงข้อมูล portal"   "$ADMIN" /portal               200 "$SID"
t "admin /research มีกล่องแก้ไข"     "$ADMIN" /research             200 "<textarea"
t "www ไม่เปิด /internal/config จากภายนอก" "$WWW" /internal/config  403
t "www ไม่เปิดหน้า /edit ให้คนทั่วไป"  "$WWW"   /edit                  404
t "host ที่ไม่รู้จักได้ 404"          "other.${DOMAIN}" /            404
echo "---- pass=${pass} fail=${fail}"
} | tee tests/results.txt

[[ "$(grep -c '^FAIL' tests/results.txt)" -eq 0 ]]
