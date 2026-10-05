#!/usr/bin/env bash
# Wait for GitHub to issue a certificate that actually covers the domain, then
# turn on HTTPS enforcement and run the full live check. GitHub's API has no
# "request certificate" call that works before the cert exists, so polling is
# the only option; it normally lands within the hour.
set -u
DOMAIN=annahemmerich.com
IP=185.199.108.153
REPO=maxhemmerich/annahemmerich

san() {
  echo | timeout 15 openssl s_client -connect "$IP:443" -servername "$DOMAIN" 2>/dev/null \
    | openssl x509 -noout -ext subjectAltName 2>/dev/null | tr -d '\n'
}

for i in $(seq 1 22); do
  S=$(san)
  if echo "$S" | grep -q "$DOMAIN"; then
    echo "certificate issued after ~$((i*25))s of polling:"
    echo "  $S"
    break
  fi
  echo "[$i] github still serving the wrong cert"
  sleep 25
done

if ! san | grep -q "$DOMAIN"; then
  echo
  echo "RESULT: certificate not issued yet. Nothing is broken — http works and"
  echo "GitHub will issue it on its own schedule. Re-run this script later."
  exit 1
fi

echo
echo "=== enabling HTTPS enforcement ==="
gh api -X PUT "repos/$REPO/pages" -F https_enforced=true \
  | python -c "import sys,json;d=json.load(sys.stdin);print('  https_enforced =',d.get('https_enforced'))" 2>/dev/null \
  || echo "  (enforcement call did not confirm; harmless — https works regardless)"

sleep 20
echo
echo "=== certificate actually served on the domain ==="
echo | timeout 20 openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null

echo
echo "=== http redirect now goes where? ==="
curl -sI --max-time 25 "http://$DOMAIN/" | grep -i -E "^HTTP|^location"
