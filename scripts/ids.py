#!/usr/bin/env python3
"""Id helper for authors.

  ids.py show en word "hello" intj      print the id of a word (text, part of speech[, reading])
  ids.py show en sentence "Hi there!"   print the id of a sentence, grammar, slang or character
  ids.py fix                            recompute every id in content/ and lexicon/ after text edits,
                                        and rewrite references (links, itemIds) to the new ids
"""
import sys

from common import (LEXICON, dialogue_id, dump_json, exercise_id, item_id, load_json,
                    make_id, pack_dirs, ALPHABETIC)

COMPUTE = {"items.json": item_id, "exercises.json": exercise_id, "dialogues.json": dialogue_id}


def fix():
    files = [(p, item_id) for p in sorted(LEXICON.glob("*.json"))]
    for folder in pack_dirs():
        files += [(folder / n, f) for n, f in COMPUTE.items() if (folder / n).exists()]
    renames, changed = {}, 0
    for path, compute in files:
        data = load_json(path)
        for obj in data:
            new = compute(obj)
            if obj.get("id") != new:
                renames[obj.get("id")] = new
                obj["id"] = new
                changed += 1
        dump_json(data, path)

    def swap(i):
        return renames.get(i, i)

    for folder in pack_dirs():
        for name in ("links.json", "exercises.json", "pack.json"):
            path = folder / name
            if not path.exists():
                continue
            data = load_json(path)
            for obj in data if isinstance(data, list) else [data]:
                if "from" in obj:
                    obj["from"], obj["to"] = swap(obj["from"]), swap(obj["to"])
                if "itemIds" in obj:
                    obj["itemIds"] = [swap(i) for i in obj["itemIds"]]
            dump_json(data, path)
    print(f"{changed} ids changed")


def main():
    args = sys.argv[1:]
    if args[:1] == ["fix"]:
        fix()
    elif args[:1] == ["show"] and len(args) >= 4:
        lang, kind, text, *rest = args[1:]
        if kind == "word":
            pos = rest[0] if rest else ""
            reading = "" if lang in ALPHABETIC else (rest[1] if len(rest) > 1 else "")
            print(make_id(lang, kind, text, pos, reading))
        else:
            print(make_id(lang, kind, text))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
