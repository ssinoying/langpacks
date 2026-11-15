#!/usr/bin/env python3
"""Turns open dictionaries into the lexicon: items with stable ids that packs refer to.

English inputs (in sources/, not committed):
  --levels      CSV files with headword, pos, CEFR columns: the CEFR-J Vocabulary Profile (A1–B2) and the
                Octanove Vocabulary Profile (C1–C2). Optional CoreInventory 1/2 and Threshold columns become topics.
  --grammar     CEFR-J Grammar Profile CSV. One grammar item per numbered entry (1, 1-1, 1-2 → item 1).
  --wiktionary  kaikki.org (wiktextract) English JSON Lines, plain or .gz, or "-" for stdin. Only IPA is taken.
                Streamed, so the multi-GB dump never has to sit on disk:
                curl -sL https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz | gunzip -c \
                  | python3 import_sources.py en --levels ... --wiktionary -

Outputs lexicon/en.json (words) and lexicon/en-grammar.json (grammar points).
Merge rule: fields already written (meaningVi, explanationVi, ...) are kept; the import only fills missing
fields and adds topics. Entries that leave the source lists stay in the file.

Usage: python3 import_sources.py en --levels sources/cefrj-vocabulary-profile-1.5.csv \
         sources/octanove-vocabulary-profile-c1c2-1.0.csv --grammar sources/cefrj-grammar-profile-20180315.csv
"""
import argparse
import csv
import gzip
import json
import re
import sys
from pathlib import Path

from common import LEXICON, dump_json, item_id, load_json

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Part-of-speech codes used in ids. Wiktionary already uses these; level lists are mapped onto them.
POS = {
    "noun": "noun", "verb": "verb", "vern": "verb", "be-verb": "verb", "do-verb": "verb", "have-verb": "verb",
    "modal auxiliary": "verb", "adjective": "adj", "adj": "adj", "adverb": "adv", "adv": "adv",
    "preposition": "prep", "prep": "prep", "determiner": "det", "det": "det", "article": "det",
    "pronoun": "pron", "pron": "pron", "conjunction": "conj", "conj": "conj",
    "interjection": "intj", "intj": "intj", "number": "num", "num": "num",
    "infinitive-to": "particle", "particle": "particle", "phrase": "phrase",
}
TOPIC_COLUMNS = ["CoreInventory 1", "CoreInventory 2", "Threshold"]
ORDER = ["id", "lang", "kind", "text", "reading", "partOfSpeech", "meaningVi", "explanationVi",
         "level", "frequencyRank", "register", "topics", "source"]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def first_level(*values):
    """Easiest CEFR level named in the first value that has one ('A1.2' -> A1, 'B1-B2' -> B1)."""
    for v in values:
        found = re.findall(r"[ABC][12]", v or "")
        if found:
            return min(found, key=LEVELS.index)
    return None


def read_levels(paths):
    """{(word, pos): (level, topics)}; a word listed at several levels keeps the easiest one."""
    out = {}
    for path in paths:
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
                topics = {slug(row[c]) for c in TOPIC_COLUMNS if row.get(c, "").strip()}
                # The CEFR-J list writes variants as "color/colour": keep each spelling.
                for word in row[word_c].split("/"):
                    key = (word.strip(), pos)
                    if not key[0]:
                        continue
                    old_level, old_topics = out.get(key, (level, set()))
                    out[key] = (min(level, old_level, key=LEVELS.index), old_topics | topics)
    return out


def read_grammar(path):
    """[(text, level, source)] from the CEFR-J Grammar Profile, one per numbered entry."""
    groups = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            base = row["ID"].split("-")[0].strip()
            level = first_level(row["CEFR-J Level"], row["GSELO"], row["Core Inventory"], row["FREQ*DISP"], row["EGP"])
            g = groups.setdefault(base, {"text": row["Grammatical Item"].strip(), "code": row["Shorthand Code"],
                                         "levels": []})
            if level:
                g["levels"].append(level)
    out, seen = [], {}
    for base, g in groups.items():
        if not g["levels"] or not g["text"]:
            continue
        seen.setdefault(g["text"], []).append(base)
        out.append([g["text"], min(g["levels"], key=LEVELS.index), base, g["code"]])
    for row in out:  # same label on several entries (e.g. affirmative vs negative): add the code to keep ids apart
        if len(seen[row[0]]) > 1:
            row[0] = f"{row[0]} ({row[3]})"
    return [(text, level, f"cefrj-grammar:{base}") for text, level, base, _ in out]


def read_wiktionary(path, wanted):
    """{(word, pos): ipa} for the wanted keys only. Prefers a US transcription, else the first one."""
    out = {}
    words = {w for w, _ in wanted}
    word_re = re.compile(r'"word": ?"((?:[^"\\]|\\.)*)"')
    f = sys.stdin if path == "-" else gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") \
        else open(path, encoding="utf-8")
    with f:
        for line in f:
            # Cheap filter before parsing: most of the 3 GB dump is words we do not teach.
            if not any(json.loads(f'"{w}"') in words for w in word_re.findall(line)):
                continue
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


def merge(path, new_items):
    existing = {i["id"]: i for i in load_json(path)} if path.exists() else {}
    added = 0
    for item in new_items:
        old = existing.get(item["id"])
        if old is None:
            existing[item["id"]] = item
            added += 1
            continue
        for k, v in item.items():
            if k == "topics":
                old["topics"] = sorted(set(old.get("topics", [])) | set(v))
            else:
                old.setdefault(k, v)
    items = sorted(existing.values(), key=lambda i: (LEVELS.index(i["level"]), i["text"].lower(), i["id"]))
    dump_json([{k: i[k] for k in sorted(i, key=lambda k: ORDER.index(k) if k in ORDER else 99)} for i in items], path)
    return len(items), added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", choices=["en"], help="only English is wired up so far")
    ap.add_argument("--levels", nargs="+", required=True)
    ap.add_argument("--grammar")
    ap.add_argument("--wiktionary")
    ap.add_argument("--out", help="folder for the lexicon files, default lexicon/")
    args = ap.parse_args()
    out = Path(args.out) if args.out else LEXICON

    levels = read_levels(args.levels)
    ipa = read_wiktionary(args.wiktionary, levels) if args.wiktionary else {}
    words = []
    for (word, pos), (level, topics) in levels.items():
        item = {"lang": args.lang, "kind": "word", "text": word, "partOfSpeech": pos}
        item["id"] = item_id(item)
        if (word, pos) in ipa:
            item["reading"] = ipa[(word, pos)]
        item["level"] = level
        if topics:
            item["topics"] = sorted(topics)
        item["source"] = f"wiktionary:{word}"
        words.append(item)
    total, added = merge(out / f"{args.lang}.json", words)
    print(f"{args.lang}.json: {total} words ({added} new, {len(ipa)} with IPA from Wiktionary)")

    if args.grammar:
        points = []
        for text, level, source in read_grammar(args.grammar):
            item = {"lang": args.lang, "kind": "grammar", "text": text}
            item["id"] = item_id(item)
            item.update(level=level, source=source)
            points.append(item)
        total, added = merge(out / f"{args.lang}-grammar.json", points)
        print(f"{args.lang}-grammar.json: {total} grammar points ({added} new)")


if __name__ == "__main__":
    main()
