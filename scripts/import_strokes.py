#!/usr/bin/env python3
"""Builds the stroke-order and alphabet packs (phase 5).

  ja-kana           hiragana + katakana, strokes from AnimCJK (graphicsJaKana.txt)
  ja-kanji-strokes  starter kanji (80 first-grade kanji), strokes from AnimCJK (graphicsJa.txt)
  zh-hans-strokes   starter simplified hanzi, strokes from AnimCJK (graphicsZhHans.txt)
  ko-hangul         the 40 Hangul letters, strokes built here (AnimCJK has no Hangul)

Readings come from Unihan (kJapanese, kMandarin) and Sino-Vietnamese readings from kVietnamese
(falling back to the traditional variant for simplified characters).

Inputs in sources/ (not committed): animcjk-kana.jsonl, animcjk-ja-grade1.jsonl, animcjk-zhhans-basic.jsonl
(AnimCJK graphics lines {character, strokes, medians}, filtered to the characters below) and Unihan.zip.
Usage: python3 import_strokes.py
"""
import json
import math
import unicodedata
import zipfile
from collections import defaultdict

from common import CONTENT, ROOT, dump_json, exercise_id, item_id

SOURCES = ROOT / "sources"

# Short Vietnamese meanings for the starter characters (Claude-written layer; readings come from Unihan).
MEANING = {
    "一": "một", "二": "hai", "三": "ba", "四": "bốn", "五": "năm", "六": "sáu", "七": "bảy", "八": "tám",
    "九": "chín", "十": "mười", "百": "trăm", "千": "nghìn", "万": "vạn, mười nghìn", "人": "người",
    "大": "to, lớn", "小": "nhỏ", "中": "giữa, trong", "上": "trên", "下": "dưới", "左": "trái", "右": "phải",
    "口": "miệng", "日": "mặt trời, ngày", "月": "mặt trăng, tháng", "山": "núi", "水": "nước", "火": "lửa",
    "木": "cây, gỗ", "土": "đất", "天": "trời", "田": "ruộng", "目": "mắt", "手": "tay", "足": "chân",
    "耳": "tai", "心": "tim, lòng", "女": "phụ nữ", "子": "con, đứa trẻ", "王": "vua", "白": "trắng",
    "不": "không", "也": "cũng", "了": "rồi (trợ từ chỉ việc đã xong)", "在": "ở, tại", "是": "là", "有": "có",
    "我": "tôi", "你": "bạn", "他": "anh ấy", "她": "cô ấy", "们": "các (hậu tố số nhiều)", "的": "của (trợ từ)",
    "这": "này", "那": "kia, đó", "个": "cái (lượng từ)", "和": "và", "来": "đến", "去": "đi", "出": "ra",
    "入": "vào", "生": "sinh, sống", "年": "năm (thời gian)", "多": "nhiều", "少": "ít", "好": "tốt, hay",
    "开": "mở", "门": "cửa", "马": "ngựa", "车": "xe", "牛": "bò", "鸟": "chim", "鱼": "cá", "米": "gạo",
    "力": "sức", "立": "đứng", "文": "văn, chữ viết", "字": "chữ", "书": "sách", "学": "học", "工": "làm, công việc",
    "东": "đông", "西": "tây", "南": "nam", "北": "bắc", "今": "nay", "明": "sáng, rõ", "早": "sớm", "午": "trưa",
    "晚": "tối, muộn", "家": "nhà", "国": "nước, quốc gia",
    "雨": "mưa", "円": "tròn; yên (tiền Nhật)", "音": "âm thanh", "花": "hoa", "貝": "vỏ sò", "気": "khí, tinh thần",
    "休": "nghỉ", "玉": "ngọc, viên tròn", "金": "vàng, tiền", "空": "bầu trời, trống rỗng", "犬": "chó",
    "見": "nhìn, thấy", "校": "trường học", "糸": "sợi chỉ", "車": "xe", "森": "rừng rậm", "正": "đúng, chính",
    "青": "xanh", "夕": "chiều tối", "石": "đá", "赤": "đỏ", "川": "sông", "先": "trước", "草": "cỏ", "村": "làng",
    "男": "đàn ông", "竹": "tre", "虫": "côn trùng", "町": "thị trấn", "名": "tên", "本": "sách, gốc", "林": "rừng",
}


# Sino-Vietnamese readings Unihan lacks (Japanese shinjitai forms and a few common characters).
HAN_VIET_EXTRA = {"円": "viên", "気": "khí", "犬": "khuyển", "町": "đinh", "糸": "mịch", "雨": "vũ",
                  "北": "bắc", "她": "tha", "米": "mễ", "这": "giá"}


def read_unihan():
    fields = defaultdict(dict)
    wanted = {"kVietnamese", "kJapanese", "kMandarin", "kTraditionalVariant"}
    with zipfile.ZipFile(SOURCES / "Unihan.zip") as z:
        for name in ("Unihan_Readings.txt", "Unihan_Variants.txt"):
            for line in z.read(name).decode("utf-8").splitlines():
                if line.startswith("U+"):
                    code, field, value = line.split("\t", 2)
                    if field in wanted:
                        fields[chr(int(code[2:], 16))][field] = value
    return fields


def han_viet(ch, unihan):
    if ch in HAN_VIET_EXTRA:
        return HAN_VIET_EXTRA[ch]
    if "kVietnamese" in unihan.get(ch, {}):
        return unihan[ch]["kVietnamese"].split()[0]
    for variant in unihan.get(ch, {}).get("kTraditionalVariant", "").split():
        trad = chr(int(variant.split("<")[0][2:], 16))
        if "kVietnamese" in unihan.get(trad, {}):
            return unihan[trad]["kVietnamese"].split()[0]
    return None


def kana_romaji(ch):
    """Hepburn romaji from the Unicode name (HIRAGANA LETTER SMALL TU → tsu nhỏ)."""
    name = unicodedata.name(ch, "")
    if "PROLONGED SOUND MARK" in name:
        return "kéo dài nguyên âm"
    if "ITERATION MARK" in name:
        return "lặp lại chữ trước"
    syllable = name.split()[-1].lower()
    syllable = {"si": "shi", "ti": "chi", "tu": "tsu", "hu": "fu", "zi": "ji", "di": "ji", "du": "zu",
                "wi": "wi", "we": "we", "wo": "wo"}.get(syllable, syllable)
    return f"{syllable} nhỏ" if " SMALL " in name else syllable


def read_graphics(file):
    return [json.loads(line) for line in open(SOURCES / file, encoding="utf-8")]


def stroke_entries(lang, graphic):
    return {"character": graphic["character"], "lang": lang, "source": "AnimCJK (Arphic PL / LGPL)",
            "strokes": [{"path": p, "median": m} for p, m in zip(graphic["strokes"], graphic["medians"])]}


def character_item(lang, ch, level, reading=None, meaning=None, hanviet=None, explanation=None, topics=None):
    item = {"lang": lang, "kind": "character", "text": ch}
    if reading:
        item["reading"] = reading
    if meaning:
        item["meaningVi"] = meaning
    if explanation:
        item["explanationVi"] = explanation
    if hanviet:
        item["hanViet"] = hanviet
    item["level"] = level
    item["topics"] = topics or ["alphabet"]
    item["id"] = item_id(item)
    return {"id": item["id"], **{k: v for k, v in item.items() if k != "id"}}


def exercise(lang, type_, skill, level, prompt, answers, items, choices=None, explanation=None):
    e = {"lang": lang, "type": type_, "skill": skill, "level": level, "prompt": prompt}
    if choices:
        e["choices"] = choices
    e["answers"] = answers
    if explanation:
        e["explanationVi"] = explanation
    e["itemIds"] = [i["id"] for i in items]
    return {"id": exercise_id(e), **e}


def neighbours(values, i, n=3):
    """n distinct other values near position i, for multiple-choice distractors."""
    out = []
    for step in range(1, len(values)):
        for j in (i + step, i - step):
            if 0 <= j < len(values) and values[j] != values[i] and values[j] not in out:
                out.append(values[j])
            if len(out) == n:
                return out
    return out


def write_pack(lang, folder, meta, items, strokes, exercises):
    base = CONTENT / lang / "foundation" / folder
    dump_json(meta, base / "pack.json")
    dump_json(items, base / "items.json")
    dump_json(strokes, base / "strokes.json")
    dump_json(exercises, base / "exercises.json")
    print(f"{meta['id']}: {len(items)} characters, {len(exercises)} exercises")


# ---------------------------------------------------------------- kana

def build_kana():
    graphics = read_graphics("animcjk-kana.jsonl")
    items, strokes, exercises = [], [], []
    chars = [g["character"] for g in graphics]
    romaji = [kana_romaji(c) for c in chars]
    for i, g in enumerate(graphics):
        ch = g["character"]
        script = "hiragana" if "HIRAGANA" in unicodedata.name(ch, "") else "katakana"
        item = character_item("ja", ch, "N5", reading=romaji[i], topics=["alphabet", script],
                              explanation=f"Chữ {script}, đọc là \"{romaji[i]}\".")
        items.append(item)
        strokes.append(stroke_entries("ja", g))
        exercises.append(exercise("ja", "stroke-order", "strokes", "N5", ch, [ch], [item]))
        if "nhỏ" in romaji[i] or " " in romaji[i]:
            continue   # small kana and marks: no reading quiz
        exercises.append(exercise("ja", "recognize", "alphabet", "N5", f"Chữ {ch} đọc là gì?", [romaji[i]], [item],
                                  choices=sorted([romaji[i]] + neighbours(romaji, i))))
        exercises.append(exercise("ja", "listen-choose", "alphabet", "N5", ch, [ch], [item],
                                  choices=sorted([ch] + neighbours(chars, i))))
    write_pack("ja", "kana", {"id": "ja-kana", "lang": "ja", "topic": "kana", "title": "Hiragana và katakana"},
               items, strokes, exercises)


# ---------------------------------------------------------------- kanji / hanzi

def build_han(lang, file, folder, pack_id, title, level, reading_field, unihan):
    items, strokes, exercises = [], [], []
    graphics = read_graphics(file)
    meanings = [MEANING.get(g["character"], "") for g in graphics]
    for i, g in enumerate(graphics):
        ch = g["character"]
        reading = unihan.get(ch, {}).get(reading_field)
        hv = han_viet(ch, unihan)
        item = character_item(lang, ch, level, reading=reading, meaning=meanings[i] or None, hanviet=hv,
                              topics=["strokes"],
                              explanation=f"Âm Hán Việt: {hv}." if hv else None)
        items.append(item)
        strokes.append(stroke_entries(lang, g))
        exercises.append(exercise(lang, "stroke-order", "strokes", level, ch, [ch], [item]))
        if meanings[i]:
            exercises.append(exercise(lang, "recognize", "vocabulary", level, f"Chữ {ch} nghĩa là gì?", [meanings[i]],
                                      [item], choices=sorted([meanings[i]] + neighbours(meanings, i)),
                                      explanation=f"Hán Việt: {hv}." if hv else None))
    write_pack(lang, folder, {"id": pack_id, "lang": lang, "topic": "strokes", "title": title},
               items, strokes, exercises)


# ---------------------------------------------------------------- hangul (strokes built here)

def circle(cx, cy, r, n=24):
    # Starts at the top and runs counter-clockwise, the way ㅇ is written.
    return [(cx - r * math.sin(2 * math.pi * k / n), cy - r * math.cos(2 * math.pi * k / n)) for k in range(n + 1)]


def shift(strokes, dx):
    return [[(x + dx, y) for x, y in s] for s in strokes]


def narrow(strokes, x0, x1):
    """Squeeze a letter drawn in 150..870 into x0..x1 (for double consonants)."""
    return [[(x0 + (x - 150) * (x1 - x0) / 720, y) for x, y in s] for s in strokes]


G = [[(250, 250), (750, 250), (750, 800)]]
D = [[(250, 250), (760, 250)], [(260, 250), (260, 780), (780, 780)]]
B = [[(270, 220), (270, 800)], [(740, 220), (740, 800)], [(270, 500), (740, 500)], [(270, 800), (740, 800)]]
S = [[(520, 220), (250, 800)], [(500, 480), (790, 800)]]
J = [[(260, 240), (760, 240)], [(560, 240), (250, 800)], [(500, 500), (790, 800)]]

# letter: (strokes in screen space, y down, 1024 box), romanization, Vietnamese note
HANGUL = {
    "ㄱ": (G, "g/k", "Giống \"g\" đầu âm tiết, cuối âm tiết đọc như \"c\"."),
    "ㄴ": ([[(280, 220), (280, 780), (780, 780)]], "n", "Như \"n\"."),
    "ㄷ": (D, "d/t", "Giữa \"đ\" và \"t\"; cuối âm tiết đọc như \"t\"."),
    "ㄹ": ([[(250, 230), (750, 230), (750, 500)], [(250, 500), (750, 500)], [(250, 500), (250, 790), (780, 790)]],
           "r/l", "Đầu âm tiết gần \"r\" nhẹ, cuối âm tiết là \"l\"."),
    "ㅁ": ([[(260, 240), (260, 780)], [(260, 240), (760, 240), (760, 780)], [(260, 780), (760, 780)]], "m", "Như \"m\"."),
    "ㅂ": (B, "b/p", "Giữa \"b\" và \"p\"; cuối âm tiết đọc như \"p\"."),
    "ㅅ": (S, "s", "Như \"x\"; trước ㅣ đọc gần \"s\" giọng Nam."),
    "ㅇ": ([circle(512, 512, 270)], "ng", "Đầu âm tiết câm, cuối âm tiết đọc \"ng\"."),
    "ㅈ": (J, "j", "Giữa \"ch\" và \"gi\"."),
    "ㅊ": ([[(512, 150), (512, 250)]] + [[(x, y + 80) for x, y in s] for s in J], "ch", "\"ch\" bật hơi mạnh."),
    "ㅋ": (G + [[(250, 510), (750, 510)]], "k", "\"kh\" bật hơi."),
    "ㅌ": ([[(260, 240), (760, 240)], [(260, 500), (760, 500)], [(260, 240), (260, 780), (780, 780)]], "t", "\"th\" bật hơi."),
    "ㅍ": ([[(230, 250), (790, 250)], [(400, 250), (380, 760)], [(620, 250), (640, 760)], [(220, 760), (800, 760)]],
           "p", "\"ph\" nhưng bật hơi bằng môi, không phải \"f\"."),
    "ㅎ": ([[(512, 140), (512, 230)], [(260, 300), (760, 300)], circle(512, 600, 190)], "h", "Như \"h\"."),
    "ㄲ": (narrow(G, 140, 470) + narrow(G, 540, 870), "kk", "\"c\" căng, không bật hơi."),
    "ㄸ": (narrow(D, 140, 470) + narrow(D, 540, 870), "tt", "\"t\" căng, không bật hơi."),
    "ㅃ": (narrow(B, 150, 460) + narrow(B, 560, 870), "pp", "\"p\" căng, không bật hơi."),
    "ㅆ": (narrow(S, 130, 480) + narrow(S, 530, 880), "ss", "\"x\" căng, mạnh."),
    "ㅉ": (narrow(J, 130, 480) + narrow(J, 530, 880), "jj", "\"ch\" căng, không bật hơi."),
    "ㅏ": ([[(420, 150), (420, 870)], [(420, 500), (650, 500)]], "a", "Như \"a\"."),
    "ㅑ": ([[(420, 150), (420, 870)], [(420, 400), (650, 400)], [(420, 620), (650, 620)]], "ya", "Như \"ia\" đọc nhanh."),
    "ㅓ": ([[(370, 500), (600, 500)], [(600, 150), (600, 870)]], "eo", "Giữa \"ơ\" và \"o\"."),
    "ㅕ": ([[(370, 400), (600, 400)], [(370, 620), (600, 620)], [(600, 150), (600, 870)]], "yeo", "\"i\" + ㅓ."),
    "ㅗ": ([[(512, 350), (512, 620)], [(150, 620), (870, 620)]], "o", "Như \"ô\", tròn môi."),
    "ㅛ": ([[(400, 360), (400, 620)], [(620, 360), (620, 620)], [(150, 620), (870, 620)]], "yo", "\"i\" + ㅗ."),
    "ㅜ": ([[(150, 420), (870, 420)], [(512, 420), (512, 700)]], "u", "Như \"u\"."),
    "ㅠ": ([[(150, 420), (870, 420)], [(400, 420), (400, 700)], [(620, 420), (620, 700)]], "yu", "\"i\" + ㅜ."),
    "ㅡ": ([[(150, 512), (870, 512)]], "eu", "Như \"ư\"."),
    "ㅣ": ([[(512, 150), (512, 870)]], "i", "Như \"i\"."),
    "ㅐ": ([[(330, 150), (330, 870)], [(330, 500), (520, 500)], [(640, 150), (640, 870)]], "ae", "Như \"e\"."),
    "ㅒ": ([[(330, 150), (330, 870)], [(330, 400), (520, 400)], [(330, 620), (520, 620)], [(640, 150), (640, 870)]],
           "yae", "\"i\" + \"e\"."),
    "ㅔ": ([[(250, 500), (450, 500)], [(450, 150), (450, 870)], [(680, 150), (680, 870)]], "e", "Như \"ê\"; nay đọc giống ㅐ."),
    "ㅖ": ([[(250, 400), (450, 400)], [(250, 620), (450, 620)], [(450, 150), (450, 870)], [(680, 150), (680, 870)]],
           "ye", "\"i\" + \"ê\"."),
    "ㅘ": ([[(340, 400), (340, 620)], [(120, 620), (560, 620)], [(700, 150), (700, 870)], [(700, 500), (880, 500)]],
           "wa", "Như \"oa\"."),
    "ㅙ": ([[(300, 400), (300, 620)], [(100, 620), (500, 620)], [(620, 150), (620, 870)], [(620, 500), (760, 500)],
            [(860, 150), (860, 870)]], "wae", "Như \"oe\"."),
    "ㅚ": ([[(340, 400), (340, 620)], [(120, 620), (560, 620)], [(720, 150), (720, 870)]], "oe", "Nay đọc như \"uê\"."),
    "ㅝ": ([[(100, 420), (560, 420)], [(330, 420), (330, 700)], [(560, 520), (700, 520)], [(720, 150), (720, 870)]],
           "wo", "Như \"uơ\"."),
    "ㅞ": ([[(80, 420), (480, 420)], [(280, 420), (280, 700)], [(480, 520), (600, 520)], [(620, 150), (620, 870)],
            [(860, 150), (860, 870)]], "we", "Như \"uê\"."),
    "ㅟ": ([[(100, 420), (560, 420)], [(330, 420), (330, 700)], [(720, 150), (720, 870)]], "wi", "Như \"uy\"."),
    "ㅢ": ([[(100, 560), (600, 560)], [(740, 150), (740, 870)]], "ui", "Như \"ưi\"."),
}
VOWELS = set("ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣㅐㅒㅔㅖㅘㅙㅚㅝㅞㅟㅢ")


def outline(median, width=70):
    """Closed polygon around a centre line: the stroke shape drawn and animated by the app."""
    pts = median
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length * width / 2, dx / length * width / 2
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    ring = left + right[::-1]
    return "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in ring) + " Z"


def to_font_space(points):
    """Screen space (y down) → the AnimCJK/Make Me a Hanzi space the app renders (y up, flipped at 900)."""
    return [(x, 900 - y) for x, y in points]


def build_hangul():
    items, strokes, exercises = [], [], []
    letters = list(HANGUL)
    romans = [HANGUL[c][1] for c in letters]
    for i, ch in enumerate(letters):
        lines, roman, note = HANGUL[ch]
        kind = "nguyên âm" if ch in VOWELS else "phụ âm"
        item = character_item("ko", ch, "TOPIK1", reading=roman, explanation=f"{kind.capitalize()}. {note}",
                              topics=["alphabet", "hangul"])
        items.append(item)
        font = [to_font_space(s) for s in lines]
        strokes.append({"character": ch, "lang": "ko", "source": "PerfectYou (dựng tay)",
                        "strokes": [{"path": outline(s), "median": [[round(x), round(y)] for x, y in s]} for s in font]})
        exercises.append(exercise("ko", "stroke-order", "strokes", "TOPIK1", ch, [ch], [item]))
        exercises.append(exercise("ko", "recognize", "alphabet", "TOPIK1", f"Chữ {ch} đọc là gì?", [roman], [item],
                                  choices=sorted([roman] + neighbours(romans, i))))
        if ch == "ㅇ":
            continue   # silent as an initial: 아 is already the listening item of ㅏ
        # A lone letter is read by its name; a syllable makes the sound: vowels with silent ㅇ, consonants with ㅏ.
        syllable = chr(0xAC00 + (11 * 21 + "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ".index(ch)) * 28) if ch in VOWELS else \
            chr(0xAC00 + ("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ".index(ch) * 21) * 28)
        group = [c for c in letters if (c in VOWELS) == (ch in VOWELS)]
        exercises.append(exercise("ko", "listen-choose", "alphabet", "TOPIK1", syllable, [ch], [item],
                                  choices=sorted([ch] + neighbours(group, group.index(ch))),
                                  explanation=f"{syllable} = " + (f"ㅇ (câm) + {ch}" if ch in VOWELS else f"{ch} + ㅏ")))
    write_pack("ko", "hangul", {"id": "ko-hangul", "lang": "ko", "topic": "hangul", "title": "Bảng chữ cái Hangul"},
               items, strokes, exercises)


if __name__ == "__main__":
    unihan = read_unihan()
    build_kana()
    build_hangul()
    build_han("ja", "animcjk-ja-grade1.jsonl", "kanji-strokes", "ja-kanji-strokes", "Kanji lớp 1: thứ tự nét", "N5",
              "kJapanese", unihan)
    build_han("zh-hans", "animcjk-zhhans-basic.jsonl", "strokes", "zh-hans-strokes", "Hán tự cơ bản: thứ tự nét",
              "HSK1", "kMandarin", unihan)
