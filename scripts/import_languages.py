#!/usr/bin/env python3
"""Imports level-tagged word lists for the phase 6 languages into lexicon/<lang>.json.

  zh   HSK 3.0 (complete-hsk-vocabulary, MIT; pinyin and traditional forms from CC-CEDICT) → zh-hans.json, zh-hant.json
  ja   JLPT lists (open-anki-jlpt-decks, MIT) + JMdict (part of speech) + Kanjium (pitch accent) → ja.json
  ko   한국어 학습용 어휘 목록 (National Institute of Korean Language; grades A/B/C, hanja) → ko.json
  de   Goethe-Zertifikat A1–B1 lists + English Wiktionary via kaikki.org (IPA, part of speech, gender) → de.json

Sino-Vietnamese readings (hanViet) come from Unihan kVietnamese, character by character, for words written only in
hanzi/kanji/hanja. Merge rule as in import_sources.py: fields already written (meaningVi …) are kept.

Inputs in sources/ (not committed). Usage:
  python3 import_languages.py zh ja ko
  curl -sL https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl.gz | gunzip -c \\
    | python3 import_languages.py de --wiktionary -
"""
import argparse
import csv
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import LEXICON, dump_json, item_id, load_json
from import_strokes import HAN_VIET_EXTRA, read_unihan

SOURCES = Path(__file__).resolve().parent.parent / "sources"
ORDER = ["id", "lang", "kind", "text", "reading", "partOfSpeech", "meaningVi", "explanationVi", "hanViet",
         "level", "frequencyRank", "register", "topics", "source"]
LEVEL_ORDER = {lv: i for i, lv in enumerate(
    ["A1", "A2", "B1", "B2", "C1", "C2"] + [f"HSK{i}" for i in range(1, 10)] + ["N5", "N4", "N3", "N2", "N1"]
    + [f"TOPIK{i}" for i in range(1, 7)])}


def is_han(ch):
    return 0x4E00 <= ord(ch) <= 0x9FFF or 0x3400 <= ord(ch) <= 0x4DBF or 0xF900 <= ord(ch) <= 0xFAFF


def han_viet_word(text, unihan):
    """Sino-Vietnamese reading of a word written only in Chinese characters, else None."""
    if not text or not all(is_han(c) for c in text):
        return None
    parts = []
    for ch in text:
        hv = HAN_VIET_EXTRA.get(ch) or unihan.get(ch, {}).get("kVietnamese", "").split()[:1]
        if not hv:
            for variant in unihan.get(ch, {}).get("kTraditionalVariant", "").split():
                trad = chr(int(variant.split("<")[0][2:], 16))
                hv = unihan.get(trad, {}).get("kVietnamese", "").split()[:1]
                if hv:
                    break
        if not hv:
            return None
        parts.append(hv if isinstance(hv, str) else hv[0])
    return " ".join(parts)


def word(lang, text, level, source, reading=None, pos=None, hanviet=None, explanation=None, frequency=None):
    item = {"lang": lang, "kind": "word", "text": text}
    if reading:
        item["reading"] = reading
    if pos:
        item["partOfSpeech"] = pos
    if explanation:
        item["explanationVi"] = explanation
    if hanviet:
        item["hanViet"] = hanviet
    item["level"] = level
    if frequency:
        item["frequencyRank"] = frequency
    item["source"] = source
    item["id"] = item_id(item)
    return item


def save(lang, items):
    path = LEXICON / f"{lang}.json"
    existing = {i["id"]: i for i in load_json(path)} if path.exists() else {}
    merged, added = dict(existing), 0
    for item in items:
        if item["id"] in merged:
            for k, v in item.items():
                merged[item["id"]].setdefault(k, v)
        else:
            merged[item["id"]] = item
            added += 1
    rows = sorted(merged.values(), key=lambda i: (LEVEL_ORDER[i["level"]], i.get("frequencyRank", 10**9), i["text"]))
    dump_json([{k: i[k] for k in sorted(i, key=lambda k: ORDER.index(k) if k in ORDER else 99)} for i in rows], path)
    print(f"{lang}.json: {len(rows)} words ({added} new)")


def dedupe(items):
    """Same id from two list entries: keep the easiest level."""
    best = {}
    for item in items:
        if item["id"] not in best or LEVEL_ORDER[item["level"]] < LEVEL_ORDER[best[item["id"]]["level"]]:
            best[item["id"]] = item
    return list(best.values())


# ---------------------------------------------------------------- Chinese

ZH_POS = {"n": "noun", "nr": "noun", "ns": "noun", "nt": "noun", "nz": "noun", "v": "verb", "vn": "verb",
          "a": "adj", "ad": "adj", "an": "adj", "d": "adv", "r": "pron", "m": "num", "q": "classifier",
          "p": "prep", "c": "conj", "u": "particle", "e": "intj", "y": "particle", "o": "intj", "i": "phrase", "l": "phrase"}


def import_zh(unihan):
    data = json.load(open(SOURCES / "hsk-complete.json", encoding="utf-8"))
    simp, trad = [], []
    for entry in data:
        levels = [int(l[1:]) for l in entry["l"] if l.startswith("n")]   # HSK 3.0 ("n7" = levels 7–9)
        if not levels:
            continue
        level = f"HSK{min(levels)}"
        pos = next((ZH_POS[p] for p in entry.get("p", []) if p in ZH_POS), None)
        for form in entry["f"][:1]:
            pinyin = form["i"]["y"].lower()
            simp.append(word("zh-hans", entry["s"], level, f"cc-cedict:{entry['s']}", reading=pinyin, pos=pos,
                             hanviet=han_viet_word(entry["s"], unihan), frequency=entry.get("q")))
            trad.append(word("zh-hant", form["t"], level, f"cc-cedict:{form['t']}", reading=pinyin, pos=pos,
                             hanviet=han_viet_word(form["t"], unihan), frequency=entry.get("q")))
    save("zh-hans", dedupe(simp))
    save("zh-hant", dedupe(trad))


# ---------------------------------------------------------------- Japanese

# Checked in order: specific labels first ("adverb" contains "verb", "adjectival nouns" contains "noun").
JA_POS = [("pre-noun adjectival", "det"), ("adjectival nouns", "adj"), ("adjective (keiyoushi)", "adj"), ("adverb", "adv"), ("pronoun", "pron"),
          ("interjection", "intj"), ("conjunction", "conj"), ("particle", "particle"), ("counter", "classifier"),
          ("numeric", "num"), ("expressions", "phrase"), ("prefix", "prefix"), ("suffix", "suffix"),
          ("noun", "noun"), ("verb", "verb"), ("adjective", "adj")]
SMALL = set("ゃゅょぁぃぅぇぉャュョァィゥェォ")


def ja_pos_map():
    """(expression, reading) → short part of speech, from JMdict (first sense with a part of speech)."""
    out = {}
    with gzip.open(SOURCES / "JMdict_e.gz") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != "entry":
                continue
            kebs = [k.text for k in el.iter("keb")]
            rebs = [r.text for r in el.iter("reb")]
            pos_text = next((p.text for p in el.iter("pos") if p.text), "")
            short = next((s for key, s in JA_POS if key in pos_text.lower()), None)
            if short:
                for r in rebs:
                    for k in kebs + [r]:   # kana spelling too: lists often write 彼処 as あそこ
                        out.setdefault((k, r), short)
            el.clear()
    return out


def pitch_map():
    """(expression, reading) → accent number (first listed) from Kanjium."""
    out = {}
    for line in open(SOURCES / "kanjium-accents.txt", encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            m = re.match(r"\d+", parts[2])
            if m:
                out.setdefault((parts[0], parts[1]), int(m.group()))
    return out


def with_pitch(reading, accent):
    """Insert the downstep mark ꜜ after the accented mora (0 = flat, no mark)."""
    if not accent:
        return reading
    morae = []
    for ch in reading:
        if ch in SMALL and morae:
            morae[-1] += ch
        else:
            morae.append(ch)
    if accent > len(morae):
        return reading
    return "".join(morae[:accent]) + "ꜜ" + "".join(morae[accent:])


def import_ja(unihan):
    pos_of, accents, items = ja_pos_map(), pitch_map(), []
    for n in (5, 4, 3, 2, 1):
        with open(SOURCES / f"jlpt-n{n}.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                # Variants are listed as "いい; よい": keep the first spelling and reading.
                text = row["expression"].split(";")[0].strip()
                reading = row["reading"].split(";")[0].strip()
                if not text:
                    continue
                accent = accents.get((text, reading))
                items.append(word("ja", text, f"N{n}", f"jmdict:{text}", reading=with_pitch(reading, accent),
                                  pos=pos_of.get((text, reading)), hanviet=han_viet_word(text, unihan)))
    save("ja", dedupe(items))


# ---------------------------------------------------------------- Korean

KO_POS = {"명": "noun", "동": "verb", "형": "adj", "부": "adv", "대": "pron", "수": "num", "관": "det",
          "감": "intj", "조": "particle", "의": "noun", "보": "verb", "어": "suffix"}
KO_LEVEL = {"A": "TOPIK1", "B": "TOPIK3", "C": "TOPIK5"}   # beginner / intermediate / advanced


def import_ko(unihan):
    items = []
    text = (SOURCES / "nikl-vocab.txt").read_bytes().decode("cp949")
    for row in csv.DictReader(text.splitlines(), delimiter="\t"):
        grade = (row.get("등급") or "").strip()
        if grade not in KO_LEVEL:
            continue
        headword = re.sub(r"\d+$", "", row["단어"].strip())   # 가격03 → 가격 (homograph number)
        note = (row.get("풀이") or "").strip()
        hanja = note if note and all(is_han(c) for c in note) else ""   # 풀이 holds hanja or a usage hint
        pos = KO_POS.get((row.get("품사") or "").strip()[:1])
        hv = han_viet_word(hanja, unihan) if hanja else None
        items.append(word("ko", headword, KO_LEVEL[grade], "nikl:학습용어휘", pos=pos, hanviet=hv,
                          explanation=f"Hán tự: {hanja}." if hanja else None,
                          frequency=int(row["순위"]) if row["순위"].strip().isdigit() else None))
    save("ko", dedupe(items))


# ---------------------------------------------------------------- German

DE_ARTICLE = {"der": "giống đực", "die": "giống cái", "das": "giống trung"}


def goethe_entries():
    """[(lemma, level, article, plural)] from the A1/A2/B1 lists."""
    out = []
    for path in sorted((SOURCES / "goethe").glob("*.tsv")):
        level = path.name[:2].upper()
        for line in open(path, encoding="utf-8"):
            head = line.split("\t")[0].strip()
            head = re.sub(r"\(\d+\)", "", head).strip()
            plural = None
            if "," in head:
                head, plural = [p.strip() for p in head.split(",", 1)]
            article = None
            m = re.match(r"^(der|die|das)\s+(.+)$", head)
            if m:
                article, head = m.group(1), m.group(2)
            head = head.rstrip("-").strip()
            if head and " " not in head:
                out.append((head, level, article, plural))
    return out


def import_de(wiktionary):
    entries = goethe_entries()
    lemmas = {e[0] for e in entries}
    info = {}   # (lemma, pos) and lemma → (ipa, pos)
    if wiktionary:
        f = sys.stdin if wiktionary == "-" else gzip.open(wiktionary, "rt", encoding="utf-8")
        word_re = re.compile(r'"word": ?"((?:[^"\\]|\\.)*)"')
        for line in f:
            m = word_re.search(line)
            if not m or json.loads(f'"{m.group(1)}"') not in lemmas:
                continue
            entry = json.loads(line)
            if entry.get("lang_code") != "de" or entry.get("word") not in lemmas:
                continue
            pos = {"noun": "noun", "verb": "verb", "adj": "adj", "adv": "adv", "prep": "prep", "pron": "pron",
                   "conj": "conj", "intj": "intj", "num": "num", "det": "det", "article": "det",
                   "particle": "particle"}.get(entry.get("pos"))
            ipa = next((s["ipa"] for s in entry.get("sounds", []) if s.get("ipa")), None)
            info.setdefault(entry["word"], (ipa, pos))
    items = []
    for lemma, level, article, plural in entries:
        ipa, pos = info.get(lemma, (None, None))
        if article:
            pos = "noun"
        note = None
        if article:
            note = f"Danh từ {DE_ARTICLE[article]}: {article} {lemma}" + (f", số nhiều {plural}." if plural else ".")
        items.append(word("de", lemma, level, f"wiktionary:{lemma}", reading=ipa, pos=pos, explanation=note))
    save("de", dedupe(items))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("langs", nargs="+", choices=["zh", "ja", "ko", "de"])
    ap.add_argument("--wiktionary", help="kaikki German JSON Lines (.gz or - for stdin), for de")
    args = ap.parse_args()
    unihan = read_unihan() if set(args.langs) & {"zh", "ja", "ko"} else {}
    for lang in args.langs:
        {"zh": lambda: import_zh(unihan), "ja": lambda: import_ja(unihan), "ko": lambda: import_ko(unihan),
         "de": lambda: import_de(args.wiktionary)}[lang]()
