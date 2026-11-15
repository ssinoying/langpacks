# langpacks

Nội dung học, đóng gói thành `.zip` (SQLite + FTS5) và phát hành qua GitHub Release của repo public này
(`ssinoying/langpacks`, ghi trong `config.json`). Code app nằm ở repo private khác. App đọc `manifest.json`, cần gói nào tải gói đó.

- `schemas/` — JSON Schema (draft 2020-12). `manifest.schema.json` khớp với `PackManifest` trong `PerfectYouKit/Sources/Domain`.
- `sources/` — từ điển mở gốc. File lớn không commit.
- `lexicon/<lang>.json` — từ vựng đã import, mỗi từ một ID cố định. Gói tham chiếu từ bằng ID.
- `content/<lang>/<level>/<topic>/` — JSON Claude soạn. Cách soạn: [AUTHORING.md](AUTHORING.md).
- `manifest.json`, `packs.lock.json` — do `build.py` sinh, có commit. Lock giữ version, sha256 của bản đã phát hành.
- `dist/` — zip vừa build, không commit.

Tên gói: `<lang>-<level>-<topic>`, ví dụ `en-A2-travel`. Gói nền tảng không có level: `ja-kana`, `en-ipa`.

## Pipeline

Chỉ cần Python 3.9+ có sẵn trên máy, không cài thêm thư viện.

```bash
python3 scripts/import_sources.py en --levels sources/cefrj.csv --wiktionary sources/kaikki-en.jsonl
python3 scripts/validate.py
python3 scripts/build.py
scripts/release.sh
python3 -m unittest discover scripts
```

`build.py` chỉ build gói có nội dung đổi và tăng version gói đó. `release.sh` tạo release cho zip chưa phát hành,
rồi commit và push `manifest.json`. GitHub Actions (`.github/workflows/langpacks.yml`) chạy test, validate, build
cho mọi push và PR, và release khi push lên `main`.
