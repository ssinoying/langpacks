#!/usr/bin/env python3
"""Builds changed packs into dist/<id>-v<version>.zip (one SQLite file with FTS5 inside) and rewrites manifest.json.

A pack is rebuilt only when its content hash changes; then its version goes up by one. packs.lock.json keeps
version, content hash, sha256 and size of the published zip, so unchanged packs keep the exact sha256 of the
asset already on GitHub. Run validate.py first.

Usage: python3 build.py [--all]   (--all rebuilds every pack into dist/ without bumping unchanged versions)
"""
import argparse
import datetime
import hashlib
import json
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

from common import DIST, PACK_FILES, ROOT, dump_json, lexicon_items, load_json, pack_dirs

LOCK = ROOT / "packs.lock.json"
MANIFEST = ROOT / "manifest.json"
CONFIG = ROOT / "config.json"
# Bump when the SQLite layout below changes in a way old app builds cannot read.
PACK_SCHEMA = 1

DDL = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE items (id TEXT PRIMARY KEY, lang TEXT NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL,
  reading TEXT, part_of_speech TEXT, meaning_vi TEXT, explanation_vi TEXT, han_viet TEXT, level TEXT NOT NULL,
  frequency_rank INTEGER, register TEXT, status TEXT, topics TEXT, source TEXT, own INTEGER NOT NULL);
CREATE TABLE links (from_id TEXT NOT NULL, to_id TEXT NOT NULL, kind TEXT NOT NULL);
CREATE TABLE exercises (id TEXT PRIMARY KEY, type TEXT NOT NULL, skill TEXT NOT NULL, level TEXT NOT NULL,
  prompt TEXT NOT NULL, choices TEXT, answers TEXT NOT NULL, explanation_vi TEXT, item_ids TEXT);
CREATE TABLE dialogues (id TEXT PRIMARY KEY, level TEXT NOT NULL, title TEXT NOT NULL, start TEXT NOT NULL,
  nodes TEXT NOT NULL);
CREATE TABLE strokes (character TEXT NOT NULL, lang TEXT NOT NULL, strokes TEXT NOT NULL, source TEXT,
  PRIMARY KEY (character, lang));
CREATE VIRTUAL TABLE items_fts USING fts5(id UNINDEXED, text, reading, meaning_vi, explanation_vi,
  tokenize = 'unicode61 remove_diacritics 2');
"""

FIXED_TIME = (2020, 1, 1, 0, 0, 0)  # zip entries get a fixed date so the same content gives the same bytes


def js(value):
    return None if value is None else json.dumps(value, ensure_ascii=False)


def collect(folder, universe):
    """Pack data: its own files plus every item it refers to (so each pack works on its own)."""
    meta = load_json(folder / "pack.json")
    data = {name: load_json(folder / name) if (folder / name).exists() else [] for name in PACK_FILES}
    own = {i["id"] for i in data["items.json"]}
    wanted = set(meta.get("itemIds", []))
    for link in data["links.json"]:
        wanted |= {link["from"], link["to"]}
    for ex in data["exercises.json"]:
        wanted |= set(ex.get("itemIds", []))
    shared = [universe[i] for i in sorted(wanted - own)]
    return meta, data, shared


def content_hash(meta, data, shared):
    blob = json.dumps([meta, data, shared, PACK_SCHEMA], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def write_sqlite(path, meta, version, data, shared):
    db = sqlite3.connect(path)
    db.executescript(DDL)
    info = dict(id=meta["id"], version=version, lang=meta["lang"], topic=meta["topic"], title=meta["title"],
                framework=meta.get("framework"), level=meta.get("level"), schema=PACK_SCHEMA)
    db.executemany("INSERT INTO meta VALUES (?, ?)", [(k, str(v)) for k, v in info.items() if v is not None])
    for own, items in ((1, data["items.json"]), (0, shared)):
        for i in items:
            db.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                i["id"], i["lang"], i["kind"], i["text"], i.get("reading"), i.get("partOfSpeech"),
                i.get("meaningVi"), i.get("explanationVi"), i.get("hanViet"), i["level"], i.get("frequencyRank"),
                i.get("register"), i.get("status"), js(i.get("topics")), i.get("source"), own))
            db.execute("INSERT INTO items_fts VALUES (?,?,?,?,?)", (
                i["id"], i["text"], i.get("reading"), i.get("meaningVi"), i.get("explanationVi")))
    db.executemany("INSERT INTO links VALUES (?,?,?)", [(l["from"], l["to"], l["kind"]) for l in data["links.json"]])
    db.executemany("INSERT INTO exercises VALUES (?,?,?,?,?,?,?,?,?)", [(
        e["id"], e["type"], e["skill"], e["level"], e["prompt"], js(e.get("choices")), js(e["answers"]),
        e.get("explanationVi"), js(e.get("itemIds"))) for e in data["exercises.json"]])
    db.executemany("INSERT INTO dialogues VALUES (?,?,?,?,?)", [(
        d["id"], d["level"], d["title"], d["start"], js(d["nodes"])) for d in data["dialogues.json"]])
    db.executemany("INSERT INTO strokes VALUES (?,?,?,?)", [(
        s["character"], s["lang"], js(s["strokes"]), s.get("source")) for s in data["strokes.json"]])
    db.commit()
    db.execute("VACUUM")
    db.close()


def build_zip(meta, version, data, shared):
    name = f"{meta['id']}-v{version}"
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{name}.zip"
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / f"{meta['id']}.sqlite"
        write_sqlite(db, meta, version, data, shared)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            info = zipfile.ZipInfo(db.name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, db.read_bytes())
    raw = out.read_bytes()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def record(zip_path):
    """Called by release.sh after uploading: the lock must describe the exact bytes on GitHub."""
    lock = load_json(LOCK)
    pack_id, _, version = zip_path.stem.rpartition("-v")
    entry = lock.get(pack_id)
    if entry is None or entry["version"] != int(version):
        return print(f"{zip_path.name}: not the current version in packs.lock.json, lock unchanged")
    raw = zip_path.read_bytes()
    entry.update(sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
    dump_json(lock, LOCK)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="rebuild every pack into dist/")
    ap.add_argument("--record", metavar="ZIP", help="store sha256 and size of a released zip in the lock, then stop")
    args = ap.parse_args()
    if args.record:
        return record(Path(args.record))

    config = load_json(CONFIG)
    lock = load_json(LOCK) if LOCK.exists() else {}
    universe = {i["id"]: i for _, i in lexicon_items()}
    folders = pack_dirs()
    for folder in folders:
        universe.update({i["id"]: i for i in (load_json(folder / "items.json") if (folder / "items.json").exists() else [])})

    entries, built = [], []
    for folder in folders:
        meta, data, shared = collect(folder, universe)
        h = content_hash(meta, data, shared)
        entry = lock.get(meta["id"])
        changed = entry is None or entry["hash"] != h
        if changed:
            version = entry["version"] + 1 if entry else 1
            sha, size = build_zip(meta, version, data, shared)
            entry = lock[meta["id"]] = {"version": version, "hash": h, "sha256": sha, "size": size}
            built.append(f"{meta['id']}-v{version}")
        elif args.all:
            build_zip(meta, entry["version"], data, shared)

        tag = f"{meta['id']}-v{entry['version']}"
        pack = {"id": meta["id"], "lang": meta["lang"]}
        if "framework" in meta:
            pack.update(framework=meta["framework"], level=meta["level"])
        pack.update(topic=meta["topic"], title=meta["title"], version=entry["version"], minAppSchema=PACK_SCHEMA,
                    size=entry["size"], sha256=entry["sha256"], requires=meta.get("requires", []),
                    url=f"https://github.com/{config['repo']}/releases/download/{tag}/{tag}.zip")
        entries.append(pack)

    gone = set(lock) - {e["id"] for e in entries}
    for pack_id in gone:  # pack folder removed: it leaves the manifest; its releases stay on GitHub
        del lock[pack_id]

    old = load_json(MANIFEST) if MANIFEST.exists() else None
    if old is None or old["packs"] != entries:
        dump_json({"schemaVersion": 1, "generatedAt": datetime.date.today().isoformat(), "packs": entries}, MANIFEST)
    dump_json(lock, LOCK)
    print(f"built {len(built)}: {', '.join(built) or '-'}; manifest lists {len(entries)} packs")


if __name__ == "__main__":
    sys.exit(main())
