"""Shared helpers for the langpacks pipeline. Standard library only (Python 3.9+)."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # langpacks/
SCHEMAS = ROOT / "schemas"
CONTENT = ROOT / "content"
LEXICON = ROOT / "lexicon"
DIST = ROOT / "dist"

# Content files a pack folder may hold, mapped to their schema.
PACK_FILES = {
    "items.json": "item.schema.json",
    "links.json": "link.schema.json",
    "exercises.json": "exercise.schema.json",
    "dialogues.json": "dialogue.schema.json",
    "strokes.json": "stroke.schema.json",
}

# Languages written with an alphabet: the reading (IPA) is not part of a word's identity there,
# because one word has several valid transcriptions (UK/US) and the key must stay stable.
ALPHABETIC = {"en", "de"}


def normalize(text):
    """Comparison form used for ids and answer grading: NFC, lowercase, no punctuation, single spaces."""
    text = unicodedata.normalize("NFC", text).lower()
    text = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def make_id(lang, kind, *key_parts):
    key = "|".join(normalize(p or "") for p in key_parts)
    digest = hashlib.sha256(f"{lang}|{kind}|{key}".encode("utf-8")).hexdigest()[:16]
    return f"{lang}:{kind}:{digest}"


def item_id(item):
    """Expected id of an Item.

    Word keys: en/de = lemma + part of speech; zh/ja = text + reading (pitch mark ꜜ ignored), since part-of-speech
    labels differ between dictionaries; ko = text + part of speech + hanja reading (keeps homographs like
    가구 家口 / 家具 apart). Other kinds: the text.
    """
    lang, kind = item["lang"], item["kind"]
    if kind == "word":
        if lang in ALPHABETIC:
            return make_id(lang, kind, item["text"], item.get("partOfSpeech", ""), "")
        if lang == "ko":
            return make_id(lang, kind, item["text"], item.get("partOfSpeech", ""), item.get("hanViet", ""))
        return make_id(lang, kind, item["text"], "", item.get("reading", "").replace("ꜜ", ""))
    return make_id(lang, kind, item["text"])


def exercise_id(ex):
    return make_id(ex["lang"], "exercise", ex["type"], ex["prompt"])


def dialogue_id(d):
    return make_id(d["lang"], "dialogue", d["title"])


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def pack_dirs():
    """Every folder under content/ that has a pack.json."""
    return sorted(p.parent for p in CONTENT.rglob("pack.json"))


def lexicon_items():
    """Items from lexicon/<lang>.json (imported dictionary words packs refer to by id)."""
    out = []
    for path in sorted(LEXICON.glob("*.json")):
        out += [(path, item) for item in load_json(path)]
    return out


# --- Minimal JSON Schema (draft 2020-12) checker covering the keywords our schemas use. ---

_schemas = {}


def _schema(name):
    if name not in _schemas:
        _schemas[name] = load_json(SCHEMAS / name)
    return _schemas[name]


def _resolve(ref, current):
    file, _, pointer = ref.partition("#")
    doc = _schema(file) if file else current
    node = doc
    for part in filter(None, pointer.split("/")):
        node = node[part]
    return node, doc


_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}


def _type_ok(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[t])


def check(value, schema, doc=None, path="$"):
    """Returns a list of error strings. Unknown keywords are ignored."""
    doc = doc or schema
    if "$ref" in schema:
        target, tdoc = _resolve(schema["$ref"], doc)
        return check(value, target, tdoc, path)
    errs = []
    if "type" in schema and not _type_ok(value, schema["type"]):
        return [f"{path}: expected {schema['type']}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in {schema['enum']}")
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: must be {schema['const']!r}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if len(value) < schema.get("minLength", 0):
            errs.append(f"{path}: too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: too long")
    if isinstance(value, (int, float)) and "minimum" in schema and value < schema["minimum"]:
        errs.append(f"{path}: below {schema['minimum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: at most {schema['maxItems']} items")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errs.append(f"{path}: items must be unique")
        prefix = schema.get("prefixItems", [])
        for i, v in enumerate(value):
            sub = prefix[i] if i < len(prefix) else schema.get("items")
            if sub is not None:
                errs += check(v, sub, doc, f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errs.append(f"{path}: missing {key}")
        for key, deps in schema.get("dependentRequired", {}).items():
            if key in value:
                errs += [f"{path}: {key} needs {d}" for d in deps if d not in value]
        extra = schema.get("additionalProperties", True)
        for key, v in value.items():
            if key in props:
                errs += check(v, props[key], doc, f"{path}.{key}")
            elif extra is False:
                errs.append(f"{path}: unknown field {key}")
            elif isinstance(extra, dict):
                errs += check(v, extra, doc, f"{path}.{key}")
    return errs


def check_file(value, schema_name, path="$"):
    return check(value, _schema(schema_name), path=path)
