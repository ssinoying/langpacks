#!/usr/bin/env python3
"""Checks every pack under content/ plus the lexicon. Exit 1 on any error; warnings only print.

Checks: schema, id = expected hash, duplicate ids across the repo, broken references
(links, exercise itemIds, dialogue nodes, pack requires), near-duplicate sentences (> 90% same words).
"""
import sys
from collections import defaultdict

from common import (CONTENT, PACK_FILES, SCHEMAS, check, check_file, dialogue_id, exercise_id, item_id,
                    lexicon_items, load_json, normalize, pack_dirs)

PACK_META = {
    "type": "object",
    "required": ["id", "lang", "topic", "title"],
    "additionalProperties": False,
    "properties": {
        "id": {"$ref": "common.schema.json#/$defs/packId"},
        "lang": {"$ref": "common.schema.json#/$defs/lang"},
        "framework": {"$ref": "common.schema.json#/$defs/framework"},
        "level": {"$ref": "common.schema.json#/$defs/level"},
        "topic": {"type": "string"},
        "title": {"type": "string"},
        "requires": {"type": "array", "items": {"$ref": "common.schema.json#/$defs/packId"}, "uniqueItems": True},
        "itemIds": {"description": "Lexicon or other packs' items this pack teaches.",
                    "type": "array", "items": {"$ref": "common.schema.json#/$defs/id"}, "uniqueItems": True},
    },
    "dependentRequired": {"level": ["framework"], "framework": ["level"]},
}

NEAR_DUPLICATE = 0.9


def rel(path):
    return path.relative_to(CONTENT.parent)


def similarity(a, b):
    wa, wb = set(a.split()), set(b.split())
    return len(wa & wb) / max(len(wa | wb), 1)


def validate():
    errors, warnings = [], []
    defined = {}                       # id -> where
    refs = []                          # (id, where)
    sentences = []                     # (normalized, id)
    pack_ids, requires = {}, []

    def define(id_, where):
        if id_ in defined:
            errors.append(f"{where}: duplicate id {id_} (also in {defined[id_]})")
        else:
            defined[id_] = where

    def add_item(item, where):
        expected = item_id(item)
        if item["id"] != expected:
            errors.append(f"{where}: id should be {expected}")
        define(item["id"], where)
        if item["kind"] == "sentence":
            sentences.append((normalize(item["text"]), item["id"]))

    for path, item in lexicon_items():
        where = f"{rel(path)}:{item.get('text', '?')}"
        errs = check_file(item, "item.schema.json", where)
        errors.extend(errs)
        if not errs:
            add_item(item, where)

    for folder in pack_dirs():
        meta = load_json(folder / "pack.json")
        errs = check(meta, PACK_META, load_json(SCHEMAS / "common.schema.json"), f"{rel(folder)}/pack.json")
        errors.extend(errs)
        if errs:
            continue
        if meta["id"] in pack_ids:
            errors.append(f"{rel(folder)}: duplicate pack id {meta['id']}")
        pack_ids[meta["id"]] = folder
        requires += [(r, rel(folder)) for r in meta.get("requires", [])]
        refs += [(r, f"{rel(folder)}/pack.json") for r in meta.get("itemIds", [])]

        for name, schema in PACK_FILES.items():
            path = folder / name
            if not path.exists():
                continue
            for i, obj in enumerate(load_json(path)):
                where = f"{rel(path)}[{i}]"
                errs = check_file(obj, schema, where)
                errors.extend(errs)
                if errs:
                    continue
                if obj.get("lang", meta["lang"]) != meta["lang"]:
                    errors.append(f"{where}: lang differs from pack lang {meta['lang']}")
                if name == "items.json":
                    add_item(obj, where)
                elif name == "links.json":
                    refs += [(obj["from"], where), (obj["to"], where)]
                elif name == "exercises.json":
                    if obj["id"] != exercise_id(obj):
                        errors.append(f"{where}: id should be {exercise_id(obj)}")
                    define(obj["id"], where)
                    refs += [(r, where) for r in obj.get("itemIds", [])]
                    if obj.get("choices") and not set(obj["answers"]) <= set(obj["choices"]):
                        errors.append(f"{where}: answers must be among choices")
                elif name == "dialogues.json":
                    if obj["id"] != dialogue_id(obj):
                        errors.append(f"{where}: id should be {dialogue_id(obj)}")
                    define(obj["id"], where)
                    nodes = obj["nodes"]
                    if obj["start"] not in nodes:
                        errors.append(f"{where}: start node {obj['start']} missing")
                    for key, node in nodes.items():
                        for opt in node.get("options", []):
                            if opt["next"] not in nodes:
                                errors.append(f"{where}: node {key} points to missing {opt['next']}")
                elif name == "strokes.json":
                    define(f"stroke:{obj['lang']}:{obj['character']}", where)

    for id_, where in refs:
        if id_ not in defined:
            errors.append(f"{where}: broken reference {id_}")
    for pack, where in requires:
        if pack not in pack_ids:
            errors.append(f"{where}: requires unknown pack {pack}")

    # shortcut: O(n²) over sentences, fine for a few thousand; bucket by first word if it gets slow.
    for i, (a, ida) in enumerate(sentences):
        for b, idb in sentences[i + 1:]:
            if similarity(a, b) > NEAR_DUPLICATE:
                warnings.append(f"near-duplicate sentences {ida} / {idb}: {a!r} ~ {b!r}")

    return errors, warnings, len(pack_ids), len(defined)


def main():
    errors, warnings, packs, ids = validate()
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{packs} packs, {ids} ids, {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
