# Soạn nội dung

Hướng dẫn cho Claude (và người) khi soạn gói. Từ vựng lấy từ từ điển mở; Claude chỉ viết lớp trên:
câu ví dụ, giải thích tiếng Việt, slang, hội thoại, bài tập kèm đáp án. Không tự bịa từ vựng.

## Quy trình

1. Từ vựng nằm trong `lexicon/<lang>.json`, điểm ngữ pháp trong `lexicon/<lang>-grammar.json`, do
   `scripts/import_sources.py` sinh ra, đã có cấp độ và chủ đề. Gói dạy mục nào thì liệt kê ID trong `itemIds`
   của `pack.json`. `meaningVi`, `explanationVi` của mục lexicon viết thẳng vào file lexicon (một mục chỉ định
   nghĩa một chỗ); import sau giữ nguyên trường đã viết. Từ chưa có thì thêm tay với `source` trỏ về Wiktionary.
2. Tạo thư mục gói: `content/<lang>/<level>/<topic>/` (gói nền tảng: `content/<lang>/foundation/<topic>/`).
3. Viết `pack.json` và các file nội dung bên dưới.
4. Tính ID: `python3 scripts/ids.py show en sentence "Nice to meet you."`. Sửa chữ của mục đã có thì chạy
   `python3 scripts/ids.py fix` để tính lại ID và sửa mọi tham chiếu.
5. `python3 scripts/validate.py` phải 0 lỗi. Đọc kỹ cảnh báo câu gần giống.
6. `python3 scripts/build.py` để thử đóng gói. Commit JSON, `manifest.json`, `packs.lock.json`. Không commit `dist/`.

## File trong một gói

| File | Nội dung | Schema |
| --- | --- | --- |
| `pack.json` | `id`, `lang`, `framework` + `level` (bỏ cả hai với gói nền tảng), `topic`, `title`, `requires`, `itemIds` (từ trong lexicon mà gói dạy) | trong `validate.py` |
| `items.json` | câu, điểm ngữ pháp, slang, ký tự của riêng gói | `item.schema.json` |
| `links.json` | nối từ → câu, câu → ngữ pháp, câu sách → cách nói đời thực | `link.schema.json` |
| `exercises.json` | bài tập, luôn có đáp án | `exercise.schema.json` |
| `dialogues.json` | hội thoại nhiều nhánh | `dialogue.schema.json` |
| `strokes.json` | thứ tự nét | `stroke.schema.json` |

Mục được tham chiếu (qua `links`, `itemIds`) mà nằm ở lexicon hay gói khác sẽ được chép vào gói lúc build,
nên mỗi gói tự đủ. Trong repo, mỗi mục chỉ định nghĩa một lần.

## ID

`<lang>:<kind>:<16 hex đầu của sha256("lang|kind|khoá")>`, khoá đã chuẩn hóa (NFC, chữ thường, bỏ dấu câu,
gộp khoảng trắng).

- Từ: chữ gốc + từ loại. Thêm cách đọc với zh, ja, ko. Tiếng Anh, Đức không đưa IPA vào khoá vì một từ có
  nhiều cách phiên âm.
- Câu, ngữ pháp, slang, ký tự: chính `text`.
- Bài tập: `type` + `prompt`. Hội thoại: `title`.

Từ loại dùng: `noun verb adj adv prep det pron conj intj num particle phrase`.

## Cách viết

- Giải thích bằng tiếng Việt, ngắn, một ý. Luôn đối chiếu với tiếng Việt: chỗ giống, chỗ khác, lỗi người Việt hay mắc.
- Câu ví dụ là câu người bản xứ nói thật, đúng cấp. Mỗi câu có `meaningVi`.
- Mỗi từ trong `itemIds` có ít nhất một câu nối tới nó (`word-sentence`).
- Ngữ pháp rút ra từ câu đã có trong gói, nối bằng `sentence-grammar`.
- Slang: ghi `register` (`casual`, `slang`, `vulgar`) và `status` (`current`, `trending`, `dated`), giải thích
  khi nào dùng và khi nào không. Nối câu sách với slang bằng `book-reallife`.

## Bài tập

Mỗi bài có `answers` liệt kê mọi đáp án chấp nhận. App so sau khi chuẩn hóa (hoa thường, dấu câu, khoảng trắng, NFC),
nên không cần liệt kê biến thể chỉ khác dấu câu. Có `choices` thì đáp án phải nằm trong `choices`.

| type | skill thường đi kèm | prompt | answers |
| --- | --- | --- | --- |
| `listen-choose` | pronunciation, listening | chữ app đọc lên | lựa chọn đúng |
| `recognize` | alphabet, pronunciation | câu hỏi | lựa chọn đúng |
| `fill-blank` | vocabulary, grammar | câu có `___`, gợi ý tiếng Việt trong ngoặc | từ điền vào |
| `reorder` | grammar, sentence | các mảnh cách nhau bằng ` / ` | câu đúng |
| `translate` | writing | câu tiếng Việt | mọi bản dịch chấp nhận |
| `dictation` | listening | câu app đọc lên | câu đó |
| `read-aloud` | speaking | câu cần đọc | câu đó |
| `comprehension` | reading | đoạn văn, dòng trống, câu hỏi | lựa chọn đúng |
| `context-choice` | reallife | tình huống | câu hợp ngữ cảnh |
| `stroke-order` | strokes | ký tự | ký tự |

Thêm `explanationVi` khi người học dễ sai, giải thích vì sao.

## Hội thoại

`nodes` là các lượt nói; `options` là câu người học có thể đáp, mỗi option nhiều `answers` chấp nhận và
`next` trỏ tới lượt kế. Lượt không có `options` là kết thúc. Nên có ít nhất một chỗ rẽ nhánh.
