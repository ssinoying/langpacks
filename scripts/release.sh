#!/usr/bin/env bash
# Publishes every zip in dist/ whose release tag does not exist yet, then commits and pushes
# manifest.json + packs.lock.json. Needs gh logged in (or GH_TOKEN in CI) with write access to the repo.
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
    # The zip must be byte-identical to what manifest.json promises, or the app rejects it.
    want=$(python3 -c 'import json,sys; t=sys.argv[1]; print(next((p["sha256"] for p in json.load(open("manifest.json"))["packs"] if p["id"] + "-v" + str(p["version"]) == t), ""))' "$tag")
    have=$(shasum -a 256 "$zip" | cut -d" " -f1)
    if [[ "$want" != "$have" ]]; then
      echo "error: $zip sha256 $have does not match manifest.json ($want). Rebuild and release from the machine that wrote packs.lock.json." >&2
      exit 1
    fi
    gh release create "$tag" "$zip" --repo "$repo" --title "$tag" --notes "Content pack $tag"
  fi
done

if [[ -n "$(git status --porcelain -- manifest.json packs.lock.json)" ]]; then
  git add manifest.json packs.lock.json
  git commit -m "langpacks: update manifest [skip ci]"
  git push
fi
