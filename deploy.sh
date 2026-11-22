#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

die() { echo "ERROR: $*" >&2; exit 1; }

command -v kubectl >/dev/null || die "ไม่พบ kubectl"
kubectl cluster-info >/dev/null 2>&1 || die "kubectl ต่อ cluster ไม่ได้ (ตรวจ kubectl config current-context)"
echo "==> context: $(kubectl config current-context)"

if ! kubectl get ingressclass nginx >/dev/null 2>&1; then
  die "ยังไม่มี IngressClass 'nginx' -> ติดตั้ง ingress-nginx ก่อน (ดู README ข้อ 1)"
fi

echo "==> Apply (kubectl apply -k .)"
kubectl apply -k .

if [[ "${1:-}" == "--restart" ]]; then
  kubectl rollout restart deployment/portal-367 deployment/app-research deployment/api-367 deployment/admin-367
fi

echo "==> รอ pod พร้อม"
for d in portal-367 app-research api-367 admin-367; do kubectl rollout status "deployment/$d" --timeout=180s; done

cat <<MSG

เสร็จแล้ว. ดูผลทดสอบด้วย:  kubectl logs -f job/ingress-check --pod-running-timeout=180s
ถ้าจะเปิดด้วยเบราว์เซอร์ ทำตาม README ข้อ 3
MSG
