#!/usr/bin/env python3
"""Writes the first greetings pack for each phase 6 language (Claude-authored layer over the imported lexicons).

Words are looked up in lexicon/<lang>.json by text (and reading where given); a word missing from the level list is
added to the lexicon by hand with the pack's level. Re-running rewrites the packs; edit the data below, not the JSON.
Usage: python3 starter_packs.py
"""
from common import CONTENT, LEXICON, dialogue_id, dump_json, exercise_id, item_id, load_json

PACKS = {
    "zh-hans": {
        "id": "zh-hans-HSK1-greetings", "framework": "HSK", "level": "HSK1", "title": "Chào hỏi và giới thiệu",
        "requires": [],
        "words": [("你", "nǐ", "bạn, anh, chị"), ("好", "hǎo", "tốt, khỏe"), ("我", "wǒ", "tôi"), ("叫", "jiào", "gọi, tên là"),
                  ("名字", "míngzi", "tên"), ("什么", "shénme", "cái gì"), ("是", "shì", "là"), ("人", "rén", "người"),
                  ("谢谢", "xièxie", "cảm ơn"), ("再见", "zàijiàn", "tạm biệt"), ("认识", "rènshi", "quen biết"),
                  ("高兴", "gāoxìng", "vui")],
        "sentences": [("你好！", "Xin chào!", ["你", "好"]), ("我叫明。", "Tôi tên là Minh.", ["我", "叫"]),
                      ("你叫什么名字？", "Bạn tên là gì?", ["你", "叫", "什么", "名字"]),
                      ("我是越南人。", "Tôi là người Việt Nam.", ["我", "是", "人"]),
                      ("认识你很高兴。", "Rất vui được biết bạn.", ["认识", "高兴"]),
                      ("谢谢！", "Cảm ơn!", ["谢谢"]), ("不客气。", "Không có gì.", []), ("再见！", "Tạm biệt!", ["再见"])],
        "grammar": [
            ("A 是 B (A là B)", "是 nối hai danh từ như \"là\" trong tiếng Việt: 我是越南人 = Tôi là người Việt Nam. "
             "Khác tiếng Việt: không dùng 是 trước tính từ. \"Tôi khỏe\" là 我很好, không nói *我是好.",
             ["我是越南人。"]),
            ("Hỏi bằng 什么: từ hỏi đứng đúng chỗ của câu trả lời",
             "Tiếng Trung giống tiếng Việt: từ hỏi nằm đúng chỗ thông tin cần hỏi. 你叫什么名字？ = Bạn tên là gì? "
             "Trả lời thì thay 什么 bằng thông tin: 我叫明。", ["你叫什么名字？", "我叫明。"]),
        ],
        "slang": [("哈喽", "casual", "current", "Chào (phiên âm từ hello).", "Giới trẻ hay dùng khi nhắn tin, gặp bạn bè.", "你好！"),
                  ("拜拜", "casual", "current", "Bye bye.", "Tạm biệt kiểu thân mật, rất phổ biến khi nói và nhắn tin.", "再见！")],
        "exercises": [
            ("fill-blank", "grammar", "我___越南人。(là)", ["是"], None, "是 nối hai danh từ."),
            ("fill-blank", "vocabulary", "你叫什么___？(tên)", ["名字"], None, None),
            ("reorder", "grammar", "名字 / 你 / 什么 / 叫", ["你叫什么名字？", "你叫什么名字"], None, "Từ hỏi 什么 đứng trước 名字."),
            ("translate", "writing", "Tôi tên là Minh.", ["我叫明。", "我叫明", "我的名字是明。"], None, None),
            ("dictation", "listening", "认识你很高兴。", ["认识你很高兴。"], None, None),
            ("read-aloud", "speaking", "你好！我叫明。", ["你好！我叫明。"], None, None),
            ("context-choice", "reallife", "Nhắn tin chào một người bạn thân. Câu nào tự nhiên nhất?", ["哈喽！"],
             ["哈喽！", "您好，先生。", "认识你很高兴。"], "Với bạn thân, 哈喽 tự nhiên; 您好，先生 rất trang trọng."),
        ],
        "dialogue": ("Làm quen", [
            ("a", "小李", "你好！我叫小李。你叫什么名字？", "Chào bạn! Mình là Tiểu Lý. Bạn tên gì?", [(["我叫明。", "我叫明", "你好，我叫明。"], "b")]),
            ("b", "小李", "认识你很高兴。你是中国人吗？", "Rất vui được biết bạn. Bạn là người Trung Quốc à?",
             [(["不是，我是越南人。", "我是越南人。"], "c")]),
            ("c", "小李", "欢迎你！再见！", "Chào mừng bạn! Tạm biệt!", [(["再见！", "拜拜！", "谢谢，再见！"], "end")]),
            ("end", "小李", "拜拜！", "Bye bye!", []),
        ]),
    },
    "ja": {
        "id": "ja-N5-greetings", "framework": "JLPT", "level": "N5", "title": "Chào hỏi và giới thiệu",
        "requires": ["ja-kana"],
        "words": [("私", "わたし", "tôi"), ("名前", "なまえ", "tên"), ("学生", "がくせい", "học sinh, sinh viên"),
                  ("先生", "せんせい", "thầy cô giáo"), ("日本", "にほん", "Nhật Bản"), ("何", "なに", "cái gì"),
                  ("ありがとう", "ありがとう", "cảm ơn"), ("さようなら", "さようなら", "tạm biệt")],
        "sentences": [("こんにちは。", "Xin chào.", []), ("はじめまして。", "Rất hân hạnh được gặp (lần đầu).", []),
                      ("私はミンです。", "Tôi là Minh.", ["私"]), ("お名前は何ですか。", "Tên bạn là gì?", ["名前", "何"]),
                      ("ベトナムから来ました。", "Tôi đến từ Việt Nam.", []), ("私は学生です。", "Tôi là sinh viên.", ["私", "学生"]),
                      ("よろしくお願いします。", "Mong được giúp đỡ.", []), ("ありがとうございます。", "Cảm ơn ạ.", ["ありがとう"]),
                      ("さようなら。", "Tạm biệt.", ["さようなら"])],
        "grammar": [
            ("A は B です (A là B)", "は (đọc là \"wa\") đánh dấu chủ đề, です là \"là\" lịch sự, đứng cuối câu. "
             "Tiếng Việt: Tôi là sinh viên → tiếng Nhật: 私は学生です (Tôi / chủ đề / sinh viên / là). Động từ, \"là\" luôn ở cuối.",
             ["私はミンです。", "私は学生です。"]),
            ("Câu hỏi: thêm か cuối câu", "Không đảo trật tự từ, chỉ thêm か vào cuối: 学生ですか = Là sinh viên à? "
             "Giống tiếng Việt thêm \"không\", \"à\" cuối câu.", ["お名前は何ですか。"]),
        ],
        "slang": [("やあ", "casual", "current", "Chào (thân mật).", "Chào bạn bè, nam giới hay dùng hơn.", "こんにちは。"),
                  ("じゃあね", "casual", "current", "Gặp lại nhé.", "Tạm biệt bạn bè. さようなら nghe xa cách, như chia tay lâu.", "さようなら。")],
        "exercises": [
            ("fill-blank", "grammar", "私___学生です。", ["は"], ["は", "が", "を", "に"], "は đánh dấu chủ đề của câu."),
            ("fill-blank", "grammar", "お名前は何です___。(câu hỏi)", ["か"], None, "Thêm か cuối câu để hỏi."),
            ("reorder", "grammar", "です / 学生 / は / 私", ["私は学生です。", "私は学生です"], None, "です luôn đứng cuối."),
            ("translate", "writing", "Tôi là Minh.", ["私はミンです。", "わたしはミンです。", "ミンです。"], None, None),
            ("dictation", "listening", "はじめまして。", ["はじめまして。"], None, None),
            ("read-aloud", "speaking", "よろしくお願いします。", ["よろしくお願いします。"], None, None),
            ("context-choice", "reallife", "Chia tay một người bạn, mai lại gặp. Câu nào tự nhiên?", ["じゃあね。"],
             ["さようなら。", "じゃあね。", "はじめまして。"], "さようなら nghe như chia tay lâu, với bạn hằng ngày dùng じゃあね."),
        ],
        "dialogue": ("Lần đầu gặp mặt", [
            ("a", "田中", "はじめまして。田中です。", "Rất hân hạnh. Tôi là Tanaka.",
             [(["はじめまして。ミンです。", "はじめまして。私はミンです。", "ミンです。"], "b")]),
            ("b", "田中", "ミンさんは学生ですか。", "Anh Minh là sinh viên à?",
             [(["はい、学生です。", "はい、そうです。"], "c"), (["いいえ、先生です。"], "c")]),
            ("c", "田中", "よろしくお願いします。", "Mong được giúp đỡ.", [(["よろしくお願いします。", "こちらこそ。"], "end")]),
            ("end", "田中", "では、また。", "Vậy hẹn gặp lại.", []),
        ]),
    },
    "ko": {
        "id": "ko-TOPIK1-greetings", "framework": "TOPIK", "level": "TOPIK1", "title": "Chào hỏi và giới thiệu",
        "requires": ["ko-hangul"],
        "words": [("이름", None, "tên"), ("학생", None, "học sinh, sinh viên"), ("선생님", None, "thầy cô giáo"),
                  ("사람", None, "người"), ("나라", None, "đất nước"), ("저", None, "tôi (khiêm tốn)"),
                  ("감사하다", None, "cảm ơn"), ("만나다", None, "gặp")],
        "sentences": [("안녕하세요.", "Xin chào.", []), ("저는 민이에요.", "Tôi là Minh.", ["저"]),
                      ("이름이 뭐예요?", "Tên bạn là gì?", ["이름"]), ("베트남 사람이에요.", "Tôi là người Việt Nam.", ["사람"]),
                      ("저는 학생이에요.", "Tôi là sinh viên.", ["저", "학생"]), ("만나서 반가워요.", "Rất vui được gặp bạn.", ["만나다"]),
                      ("감사합니다.", "Cảm ơn ạ.", ["감사하다"]), ("안녕히 가세요.", "Đi bình an nhé (nói với người ra về).", [])],
        "grammar": [
            ("N이에요 / N예요 (là N)", "Gắn sau danh từ để nói \"là\": danh từ có patchim (phụ âm cuối) dùng 이에요, "
             "không có dùng 예요. 학생이에요 (sinh viên), 의사예요 (bác sĩ). \"Là\" đứng cuối câu, khác tiếng Việt.",
             ["저는 학생이에요.", "저는 민이에요."]),
            ("은/는: đánh dấu chủ đề", "저는 = \"còn tôi thì\". Có patchim dùng 은, không có dùng 는. "
             "Tiếng Việt không có trợ từ này, nghĩa gần với \"thì\": Tôi thì là sinh viên.", ["저는 학생이에요."]),
        ],
        "slang": [("안녕!", "casual", "current", "Chào!", "Chào bạn bè hoặc người nhỏ tuổi hơn. Với người lớn phải nói 안녕하세요.", "안녕하세요."),
                  ("ㅎㅇ", "slang", "current", "Hi (nhắn tin).", "Viết tắt của 하이 (hi) khi nhắn tin, chỉ dùng với bạn thân.", "안녕하세요.")],
        "exercises": [
            ("fill-blank", "grammar", "저는 학생___. (là)", ["이에요"], ["이에요", "예요", "은", "는"], "학생 có patchim ㅇ nên dùng 이에요."),
            ("fill-blank", "grammar", "저___ 민이에요. (chủ đề)", ["는"], ["은", "는", "이", "가"], "저 không có patchim nên dùng 는."),
            ("reorder", "grammar", "학생이에요 / 저는", ["저는 학생이에요.", "저는 학생이에요"], None, None),
            ("translate", "writing", "Tôi là người Việt Nam.", ["베트남 사람이에요.", "저는 베트남 사람이에요."], None, None),
            ("dictation", "listening", "만나서 반가워요.", ["만나서 반가워요."], None, None),
            ("read-aloud", "speaking", "안녕하세요. 저는 민이에요.", ["안녕하세요. 저는 민이에요."], None, None),
            ("context-choice", "reallife", "Gặp giáo sư ở trường. Câu nào đúng?", ["안녕하세요."],
             ["안녕!", "ㅎㅇ", "안녕하세요."], "안녕 và ㅎㅇ chỉ dùng với bạn bè."),
        ],
        "dialogue": ("Làm quen ở lớp học", [
            ("a", "지수", "안녕하세요! 저는 지수예요. 이름이 뭐예요?", "Xin chào! Mình là Jisu. Bạn tên gì?",
             [(["저는 민이에요.", "민이에요.", "안녕하세요. 저는 민이에요."], "b")]),
            ("b", "지수", "어느 나라 사람이에요?", "Bạn là người nước nào?", [(["베트남 사람이에요.", "저는 베트남 사람이에요."], "c")]),
            ("c", "지수", "만나서 반가워요!", "Rất vui được gặp bạn!", [(["저도 반가워요.", "만나서 반가워요."], "end")]),
            ("end", "지수", "안녕히 가세요!", "Về bình an nhé!", []),
        ]),
    },
    "de": {
        "id": "de-A1-greetings", "framework": "CEFR", "level": "A1", "title": "Chào hỏi và giới thiệu",
        "requires": [],
        "words": [("Name", None, "tên"), ("heißen", None, "tên là, gọi là"), ("kommen", None, "đến"), ("aus", None, "từ (đâu)"),
                  ("danke", None, "cảm ơn"), ("bitte", None, "làm ơn; không có gì"), ("gut", None, "tốt, khỏe"),
                  ("tschüss", None, "tạm biệt (thân mật)")],
        "sentences": [("Hallo! Ich heiße Lan.", "Xin chào! Tôi tên là Lan.", ["heißen"]), ("Wie heißen Sie?", "Ông/bà tên là gì?", ["heißen"]),
                      ("Wie heißt du?", "Bạn tên gì?", ["heißen"]), ("Ich komme aus Vietnam.", "Tôi đến từ Việt Nam.", ["kommen", "aus"]),
                      ("Wie geht es Ihnen?", "Ông/bà có khỏe không?", []), ("Gut, danke.", "Khỏe, cảm ơn.", ["gut", "danke"]),
                      ("Freut mich.", "Rất vui được gặp.", []), ("Auf Wiedersehen!", "Tạm biệt!", []), ("Tschüss!", "Chào nhé!", ["tschüss"])],
        "grammar": [
            ("du và Sie", "du = bạn (thân mật: bạn bè, gia đình, trẻ em); Sie (viết hoa) = ông/bà/anh/chị (lịch sự: người lạ, "
             "đồng nghiệp, cấp trên). Động từ đổi theo: Wie heißt du? / Wie heißen Sie? Tiếng Việt đổi đại từ xưng hô, "
             "tiếng Đức đổi cả đuôi động từ.", ["Wie heißen Sie?", "Wie heißt du?"]),
            ("Chia động từ: ich heiße, du heißt, Sie heißen", "Động từ đổi đuôi theo ngôi: ich -e, du -st (heißen → heißt), "
             "Sie/wir -en. ich komme, du kommst, Sie kommen. Tiếng Việt không chia động từ, đây là lỗi hay gặp.",
             ["Hallo! Ich heiße Lan.", "Ich komme aus Vietnam."]),
        ],
        "slang": [("Na?", "casual", "current", "Sao rồi?", "Chào bạn bè kiểu \"thế nào rồi?\", trả lời: Gut! hoặc Na?", "Wie geht es Ihnen?"),
                  ("Servus!", "casual", "current", "Chào! / Tạm biệt!", "Dùng ở miền Nam Đức và Áo, vừa để chào vừa để tạm biệt.", "Auf Wiedersehen!")],
        "exercises": [
            ("fill-blank", "grammar", "Wie ___ du? (heißen)", ["heißt"], None, "Với du, heißen thành heißt."),
            ("fill-blank", "grammar", "Ich ___ aus Vietnam. (kommen)", ["komme"], None, "Với ich, động từ thêm -e."),
            ("reorder", "grammar", "Sie / heißen / wie", ["Wie heißen Sie?", "Wie heißen Sie"], None, "Từ hỏi đứng đầu, động từ đứng thứ hai."),
            ("translate", "writing", "Tôi đến từ Việt Nam.", ["Ich komme aus Vietnam.", "Ich komme aus Vietnam"], None, None),
            ("dictation", "listening", "Wie geht es Ihnen?", ["Wie geht es Ihnen?"], None, None),
            ("read-aloud", "speaking", "Hallo! Ich heiße Lan.", ["Hallo! Ich heiße Lan."], None, None),
            ("context-choice", "reallife", "Gặp sếp mới ở công ty. Câu nào phù hợp?", ["Guten Tag! Wie heißen Sie?"],
             ["Na?", "Guten Tag! Wie heißen Sie?", "Servus, wie heißt du?"], "Với sếp và người lạ dùng Sie."),
        ],
        "dialogue": ("Làm quen", [
            ("a", "Anna", "Hallo! Ich heiße Anna. Wie heißt du?", "Chào! Mình là Anna. Bạn tên gì?",
             [(["Ich heiße Lan.", "Hallo, ich heiße Lan.", "Ich bin Lan."], "b")]),
            ("b", "Anna", "Freut mich! Woher kommst du?", "Rất vui! Bạn đến từ đâu?", [(["Ich komme aus Vietnam.", "Aus Vietnam."], "c")]),
            ("c", "Anna", "Toll! Bis später!", "Tuyệt! Hẹn gặp lại!", [(["Tschüss!", "Bis später!", "Tschüss, Anna!"], "end")]),
            ("end", "Anna", "Tschüss!", "Chào nhé!", []),
        ]),
    },
}

# Traditional-Chinese mirror of the simplified pack: same lesson, traditional spelling.
TRAD = {"你好！": "你好！", "我叫明。": "我叫明。", "你叫什么名字？": "你叫什麼名字？", "我是越南人。": "我是越南人。",
        "认识你很高兴。": "認識你很高興。", "谢谢！": "謝謝！", "不客气。": "不客氣。", "再见！": "再見！",
        "什么": "什麼", "谢谢": "謝謝", "再见": "再見", "认识": "認識", "高兴": "高興", "名字": "名字",
        "哈喽": "哈囉", "拜拜": "拜拜", "小李": "小李"}


def to_trad(text):
    for s, t in sorted(TRAD.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(s, t)
    for s, t in {"么": "麼", "认": "認", "识": "識", "兴": "興", "谢": "謝", "见": "見", "气": "氣", "欢": "歡", "迎": "迎",
                 "吗": "嗎", "国": "國", "这": "這", "们": "們", "李": "李", "拜": "拜", "喽": "囉"}.items():
        text = text.replace(s, t)
    return text


def trad_pack():
    src = PACKS["zh-hans"]
    conv = lambda x: to_trad(x) if isinstance(x, str) else x
    return {
        **src, "id": "zh-hant-HSK1-greetings",
        "words": [(to_trad(w), r, m) for w, r, m in src["words"]],
        "sentences": [(to_trad(t), vi, [to_trad(w) for w in ws]) for t, vi, ws in src["sentences"]],
        "grammar": [(to_trad(n), to_trad(e), [to_trad(s) for s in ss]) for n, e, ss in src["grammar"]],
        "slang": [(to_trad(t), r, st, m, e, to_trad(b)) for t, r, st, m, e, b in src["slang"]],
        "exercises": [(ty, sk, to_trad(p), [to_trad(a) for a in ans], [to_trad(c) for c in ch] if ch else None, e)
                      for ty, sk, p, ans, ch, e in src["exercises"]],
        "dialogue": (src["dialogue"][0], [(k, to_trad(sp), to_trad(tx), vi, [([to_trad(a) for a in ans], nx) for ans, nx in opts])
                                          for k, sp, tx, vi, opts in src["dialogue"][1]]),
    }


def build(lang, spec):
    lexicon_path = LEXICON / f"{lang}.json"
    lexicon = load_json(lexicon_path)
    level, topic = spec["level"], "greetings"
    words, lexicon_changed = {}, False
    for text, reading, meaning in spec["words"]:
        def plain(r):   # compare readings without pitch marks or syllable spaces ("míng zi" = "míngzi")
            return r.replace("ꜜ", "").replace(" ", "")
        hit = next((i for i in lexicon if i["text"] == text and (reading is None or plain(i.get("reading", "")) == plain(reading))), None)
        if hit is None:
            hit = {"lang": lang, "kind": "word", "text": text, **({"reading": reading} if reading else {}), "level": level,
                   "source": "manual"}
            hit["id"] = item_id(hit)
            lexicon.append(hit)
        if "meaningVi" not in hit:
            hit["meaningVi"] = meaning
            lexicon_changed = True
        topics = set(hit.get("topics", [])) | {topic}
        if topics != set(hit.get("topics", [])):
            hit["topics"] = sorted(topics)
            lexicon_changed = True
        words[text] = hit
    if lexicon_changed:
        dump_json(lexicon, lexicon_path)

    def item(kind, text, **kw):
        i = {"lang": lang, "kind": kind, "text": text, **kw, "level": level, "topics": [topic]}
        return {"id": item_id(i), **i}

    sentences = {t: item("sentence", t, meaningVi=vi) for t, vi, _ in spec["sentences"]}
    grammar = [item("grammar", n, explanationVi=e) for n, e, _ in spec["grammar"]]
    slang = [item("slang", t, meaningVi=m, explanationVi=e, register=r, status=st) for t, r, st, m, e, _ in spec["slang"]]

    links = []
    for t, _, ws in spec["sentences"]:
        links += [{"from": words[w]["id"], "to": sentences[t]["id"], "kind": "word-sentence"} for w in ws if w in words]
    for g, (_, _, ss) in zip(grammar, spec["grammar"]):
        links += [{"from": sentences[s]["id"], "to": g["id"], "kind": "sentence-grammar"} for s in ss if s in sentences]
    for sl, row in zip(slang, spec["slang"]):
        if row[5] in sentences:
            links.append({"from": sentences[row[5]]["id"], "to": sl["id"], "kind": "book-reallife"})

    exercises = []
    for ty, sk, prompt, answers, choices, expl in spec["exercises"]:
        e = {"lang": lang, "type": ty, "skill": sk, "level": level, "prompt": prompt}
        if choices:
            e["choices"] = choices
        e["answers"] = answers
        if expl:
            e["explanationVi"] = expl
        exercises.append({"id": exercise_id(e), **e})

    title, nodes = spec["dialogue"]
    d = {"lang": lang, "level": level, "title": title, "start": nodes[0][0],
         "nodes": {k: {"speaker": sp, "text": tx, "translationVi": vi,
                       **({"options": [{"answers": a, "next": n} for a, n in opts]} if opts else {})}
                   for k, sp, tx, vi, opts in nodes}}
    dialogue = {"id": dialogue_id(d), **d}

    base = CONTENT / lang / level / topic
    dump_json({"id": spec["id"], "lang": lang, "framework": spec["framework"], "level": level, "topic": topic,
               "title": spec["title"], "requires": spec["requires"], "itemIds": [w["id"] for w in words.values()]},
              base / "pack.json")
    dump_json(list(sentences.values()) + grammar + slang, base / "items.json")
    dump_json(links, base / "links.json")
    dump_json(exercises, base / "exercises.json")
    dump_json([dialogue], base / "dialogues.json")
    print(f"{spec['id']}: {len(words)} words, {len(sentences)} sentences, {len(exercises)} exercises")


if __name__ == "__main__":
    for lang, spec in PACKS.items():
        build(lang, spec)
    build("zh-hant", trad_pack())
