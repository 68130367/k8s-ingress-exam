#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

kubectl delete -k . --ignore-not-found
kubectl delete pv -l app.kubernetes.io/part-of=k8s-ingress-exam --ignore-not-found
