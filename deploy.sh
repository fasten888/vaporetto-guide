#!/usr/bin/env bash
# Build and validate the site locally. Deployment itself is `git push` (GitHub Actions).
#
#   ./deploy.sh                          # GitHub Pages project URL
#   ./deploy.sh https://vaporettoguide.com   # custom domain at the root

set -euo pipefail
cd "$(dirname "$0")"

SITE_URL="${1:-https://fasten888.github.io}"
SITE_URL="${SITE_URL%/}"

if [ "$SITE_URL" = "https://fasten888.github.io" ]; then
  export BASE_PATH="/vaporetto-guide"
else
  export BASE_PATH=""
fi
export SITE_URL

echo "→ Building for ${SITE_URL}${BASE_PATH}/"
python3 build.py

echo
echo "→ Checks"
python3 tools/check_site.py

echo
echo "→ Local preview (rebuilds with a root base path)"
echo "  ./preview.sh"
echo
echo "→ Publish"
echo "  git add -A && git commit -m \"Update site\" && git push"
echo "  GitHub Actions rebuilds and deploys on push to main."
