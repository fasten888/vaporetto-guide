#!/usr/bin/env bash
# Smoke-test the deployed site.
#   ./verify-live.sh https://fasten888.github.io/vaporetto-guide

set -euo pipefail
BASE="${1:-https://vaporettoguide.com}"
BASE="${BASE%/}"

echo "→ ${BASE}/"
code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/")
echo "  home            ${code}"
[ "$code" = "200" ] || exit 1

for path in /tickets-and-prices/ /how-to-ride/ /pronunciation/ /etymology/ /what-is-a-vaporetto/ /vaporetto-line-1/ /vaporetto-from-marco-polo-airport/ /vaporetto-vs-gondola/ /about/ /privacy/ /sitemap.xml /robots.txt /assets/style.css; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${path}")
  printf "  %-15s %s\n" "${path#/}" "${code}"
  [ "$code" = "200" ] || exit 1
done

canonical=$(curl -s "${BASE}/" | grep -o 'rel="canonical" href="[^"]*"' | head -1)
echo "  ${canonical}"
urls=$(curl -s "${BASE}/sitemap.xml" | grep -c "<loc>")
echo "  sitemap urls    ${urls}"
[ "$urls" -ge 12 ] || exit 1

code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/this-page-does-not-exist/")
echo "  404 page        ${code}"
[ "$code" = "404" ] || exit 1

echo
echo "OK"
