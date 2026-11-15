#!/usr/bin/env python3
"""Turns open dictionaries into lexicon/<lang>.json: one Item per (word, part of speech), with a stable id.

English inputs (put them in sources/, they are not committed):
  --levels   CSV with a header that has headword, pos and CEFR columns (e.g. the CEFR-J wordlist).
  --wiktionary  Wiktionary extract in JSON Lines from kaikki.org (wiktextract): one entry per line
               with word, pos, sounds[].ipa. Streamed, so the multi-GB file is fine.

Merge rule: entries already in the lexicon keep every field Claude or a human wrote (meaningVi, ...);
the import only fills fields that are missing. Words that leave the level list stay in the file.

Usage: python3 import_sources.py en --levels sources/cefrj.csv --wiktionary sources/kaikki-en.jsonl
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from common import LEXICON, dump_json, item_id, load_json

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Part-of-speech codes used in ids. Wiktionary already uses these; level lists are mapped onto them.
POS = {
    "noun": "noun", "verb": "verb", "be-verb": "verb", "do-verb": "verb", "have-verb": "verb",
    "modal auxiliary": "verb", "adjective": "adj", "adj": "adj", "adverb": "adv", "adv": "adv",
    "preposition": "prep", "prep": "prep", "determiner": "det", "det": "det", "article": "det",
    "pronoun": "pron", "pron": "pron", "conjunction": "conj", "conj": "conj",
    "interjection": "intj", "intj": "intj", "number": "num", "num": "num",
    "infinitive-to": "particle", "particle": "particle", "phrase": "phrase",
}


def read_levels(path):
    """{(word, pos): level}; a word listed at several levels keeps the easiest one."""
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.lower().strip(): c for c in reader.fieldnames or []}
        try:
            word_c, pos_c, level_c = cols["headword"], cols["pos"], cols["cefr"]
        except KeyError:
            sys.exit(f"{path}: needs headword, pos and CEFR columns, found {reader.fieldnames}")
        for row in reader:
            level = row[level_c].strip().upper()
            pos = POS.get(row[pos_c].strip().lower())
            if level not in LEVELS or not pos:
                continue
            # The CEFR-J list writes variants as "color/colour": keep each spelling.
            for word in row[word_c].split("/"):
                key = (word.strip(), pos)
                if key[0] and (key not in out or LEVELS.index(level) < LEVELS.index(out[key])):
                    out[key] = level
    return out


def read_wiktionary(path, wanted):
    """{(word, pos): ipa} for the wanted keys only. Prefers a US transcription, else the first one."""
    out = {}
    words = {w for w, _ in wanted}
    with open(path, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            word = entry.get("word")
            if word not in words or entry.get("lang_code", "en") != "en":
                continue
            key = (word, POS.get(entry.get("pos", ""), entry.get("pos")))
            if key not in wanted or key in out:
                continue
            ipas = [s for s in entry.get("sounds", []) if s.get("ipa")]
            us = [s for s in ipas if any("US" in t or "General-American" in t for t in s.get("tags", []))]
            if ipas:
                out[key] = (us or ipas)[0]["ipa"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", choices=["en"], help="only English is wired up so far")
    ap.add_argument("--levels", required=True)
    ap.add_argument("--wiktionary")
    ap.add_argument("--out", help="default lexicon/<lang>.json")
    args = ap.parse_args()

    levels = read_levels(args.levels)
    ipa = read_wiktionary(args.wiktionary, levels) if args.wiktionary else {}

    path = Path(args.out) if args.out else LEXICON / f"{args.lang}.json"
    existing = {i["id"]: i for i in load_json(path)} if path.exists() else {}
    added = 0
    for (word, pos), level in levels.items():
        item = {"lang": args.lang, "kind": "word", "text": word, "partOfSpeech": pos}
        item["id"] = item_id(item)
        item.update(level=level, source=f"wiktionary:{word}")
        if (word, pos) in ipa:
            item["reading"] = ipa[(word, pos)]
        if item["id"] in existing:
            old = existing[item["id"]]
            for k, v in item.items():
                old.setdefault(k, v)
        else:
            existing[item["id"]] = item
            added += 1

    order = ["id", "lang", "kind", "text", "reading", "partOfSpeech", "meaningVi", "explanationVi",
             "level", "frequencyRank", "register", "topics", "source"]
    items = sorted(existing.values(), key=lambda i: (LEVELS.index(i["level"]), i["text"].lower(), i["id"]))
    items = [{k: i[k] for k in sorted(i, key=lambda k: order.index(k) if k in order else 99)} for i in items]
    dump_json(items, path)
    print(f"{path.name}: {len(items)} words ({added} new, {len(ipa)} with IPA from Wiktionary)")


if __name__ == "__main__":
    main()
