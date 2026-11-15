#!/usr/bin/env bash
# Publishes every zip in dist/ whose release tag does not exist yet, then commits and pushes
# manifest.json + packs.lock.json. SQLite writes slightly different bytes on different machines (macOS vs
# the Ubuntu CI runner), so the sha256 and size recorded for a pack are taken from the file actually uploaded. Needs gh logged in (or GH_TOKEN in CI) with write access to the repo.
# Run after: validate.py && build.py
set -euo pipefail
cd "$(dirname "$0")/.."

repo=$(python3 -c 'import json; print(json.load(open("config.json"))["repo"])')
shopt -s nullglob
for zip in dist/*.zip; do
  tag=$(basename "$zip" .zip)
  if gh release view "$tag" --repo "$repo" >/dev/null 2>&1; then
    echo "skip $tag (already released)"
  else
    gh release create "$tag" "$zip" --repo "$repo" --title "$tag" --notes "Content pack $tag"
    python3 scripts/build.py --record "$zip"
  fi
done
python3 scripts/build.py   # rewrite manifest.json from the lock

if [[ -n "$(git status --porcelain -- manifest.json packs.lock.json)" ]]; then
  git add manifest.json packs.lock.json
  git commit -m "langpacks: update manifest [skip ci]"
  git push
fi
