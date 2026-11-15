# langpacks

Nội dung học, đóng gói thành `.zip` (SQLite + FTS5) và phát hành qua GitHub Release của repo public này
(`ssinoying/langpacks`, ghi trong `config.json`). Code app nằm ở repo private khác. App đọc `manifest.json`, cần gói nào tải gói đó.

- `schemas/` — JSON Schema (draft 2020-12). `manifest.schema.json` khớp với `PackManifest` trong `PerfectYouKit/Sources/Domain`.
- `sources/` — từ điển mở gốc. File lớn không commit.
- `lexicon/<lang>.json`, `lexicon/<lang>-grammar.json` — từ vựng và điểm ngữ pháp đã import, có cấp độ và chủ đề,
  mỗi mục một ID cố định. Gói tham chiếu bằng ID.
- `content/<lang>/<level>/<topic>/` — JSON Claude soạn. Cách soạn: [AUTHORING.md](AUTHORING.md).
- `manifest.json`, `packs.lock.json` — do `build.py` sinh, có commit. Lock giữ version, sha256 của bản đã phát hành.
- `dist/` — zip vừa build, không commit.

Tên gói: `<lang>-<level>-<topic>`, ví dụ `en-A2-travel`. Gói nền tảng không có level: `ja-kana`, `en-ipa`.

## Pipeline

Chỉ cần Python 3.9+ có sẵn trên máy, không cài thêm thư viện.

```bash
python3 scripts/import_sources.py en \
  --levels sources/cefrj-vocabulary-profile-1.5.csv sources/octanove-vocabulary-profile-c1c2-1.0.csv \
  --grammar sources/cefrj-grammar-profile-20180315.csv
python3 scripts/validate.py
python3 scripts/build.py
scripts/release.sh
python3 -m unittest discover scripts
```

`build.py` chỉ build gói có nội dung đổi và tăng version gói đó. `release.sh` tạo release cho zip chưa phát hành,
rồi commit và push `manifest.json`. GitHub Actions (`.github/workflows/langpacks.yml`) chạy test, validate, build
cho mọi push và PR, và release khi push lên `main`.

Lấy IPA từ Wiktionary mà không lưu file 3,4 GB xuống đĩa:

```bash
curl -sL https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz | gunzip -c \
  | python3 scripts/import_sources.py en --levels sources/cefrj-vocabulary-profile-1.5.csv \
      sources/octanove-vocabulary-profile-c1c2-1.0.csv --wiktionary -
```

## Nguồn dữ liệu

- The CEFR-J Wordlist Version 1.5 và The CEFR-J Grammar Profile Version 20180315, Yukio Tono, Tokyo University of
  Foreign Studies, qua [Open Language Profiles](https://github.com/openlanguageprofiles/olp-en-cefrj). Dùng miễn phí,
  có trích dẫn.
- Octanove Vocabulary Profile C1/C2 1.0, Octanove Labs, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- Phát âm IPA từ [Wiktionary](https://en.wiktionary.org/) qua [kaikki.org](https://kaikki.org/) (wiktextract),
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
